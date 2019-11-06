import cv2
import numpy as np
import math
import os
import copy


class SideRecognizeError(Exception):
    def __init__(self):
        super().__init__(self, "Can't recognize the side")


class ImageRecognizer:
    PREVIEW_POINT_THICKNESS = 7
    PREVIEW_LINE_THICKNESS = 3

    FILLING_THRESHOLD = 0.5

    MASKS_PATH = 'side_masks\\'
    MASKS = {}

    def __init__(self, src_path=None, example_path=None, regions=None):
        if src_path:
            self.src_img = self.open_image(src_path)
        if example_path:
            self.example_img = self.open_image(example_path)
        self.regions = regions

    def open_image(self, path):
        path = os.path.relpath(path)
        path = path.replace('\\', '/')
        img = cv2.imread(path)
        try:
            print (img.shape)
            return img
        except:
            print('В имени файла имеется кириллица, невозможно прочитать файл')
            return None

    def set_src_img(self, path):
        self.src_img = self.open_image(path)

    def set_src_img2(self, img):
        self.src_img = img

    def start_capturing(self):
        '''Функция для определения анкеты с веб-камеры'''
        cap = cv2.VideoCapture(0)
        while(cap.isOpened()):
            k = cv2.waitKey(33)
            ret, frame = cap.read()
            pts = self.find_corners(frame)
            self.preview(frame, pts, window_title='Esc for quit, Space for commit')
            if k==27:       #Esc
                break
            elif k==32:     #Space
                 self.set_src_img2(frame)
                 return self.get_values
        cap.release()
        cv2.destroyAllWindows()

    def get_values(self):
        img = self.warp_img(self.src_img, self.example_img)
        values = self.roi_processing(img, self.regions)
        return values

    def get_contour_centroid(self, c):
        M = cv2.moments(c)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        return (cX, cY)

    def mm2square(self, value):
        vmin = (value * self.DPI * self.MM_TO_INCH) ** 2 - self.ABERRATION
        vmax = (value * self.DPI * self.MM_TO_INCH) ** 2 + self.ABERRATION
        return vmin, vmax

    def crop(self, image, size):
        end_y, end_x = image.shape[:2]
        return image[size:end_y - size, size:end_x - size]

    def pts2contour(self, pts):
        return np.asarray([[pt] for pt in pts])    

    def preprocessing_image(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.GaussianBlur(img, (5, 5), 0)
        ret, img = cv2.threshold(
            img, 50, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return img

    def handpoint(self, image, count=10):
        '''Выделение заданного количества точек вручную'''
        try:
            img = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        except cv2.error:
            img = copy.copy(image)
        points = []

        def pointNclick(event, x, y, flags, param):
            if event == cv2.cv2.EVENT_LBUTTONDOWN:
                points.append((x, y))
                print(x, y)
                cv2.circle(img, (x, y),
                           self.PREVIEW_POINT_THICKNESS, (0, 0, 255), -1)

        cv2.namedWindow('Detect %d points' % (count), cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Detect %d points' %
                         (count), 800, 600)
        cv2.setMouseCallback('Detect %d points' % (count), pointNclick)
        while (len(points) < count):
            cv2.imshow('Detect %d points' % (count), img)
            k = cv2.waitKey(1) & 0xFF
            if k == 27:
                break
        cv2.destroyAllWindows()
        return points

    def handrect(self, image, count=10):
        '''Выделение заданного областей точек вручную'''
        try:
            img = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        except cv2.error:
            img = copy.copy(image)
        drawing = False
        ix, iy = -1, -1
        splitting_regions = []
        def pointNdrag(event, x, y, flags, param):
            nonlocal ix
            nonlocal iy
            nonlocal drawing
            if event == cv2.cv2.EVENT_LBUTTONDOWN:
                drawing = True
                ix, iy = x, y
            elif event == cv2.EVENT_MOUSEMOVE:
                if drawing:
                    cv2.rectangle(img, (ix, iy), (x, y),
                                  (0, 255, 0), -1)
            elif event == cv2.EVENT_LBUTTONUP:
                drawing = False
                cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), -1)
                splitting_regions.append(
                    cv2.boundingRect(np.array([(ix, iy), (x, y)])))
                # print(abs(ix - x) * abs(iy - y))
        cv2.namedWindow('Detect %d rectangles' % (count), cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Detect %d rectangles' %
                         (count), 600, int(self.__ratio * 600))
        cv2.setMouseCallback('Detect %d rectangles' % (count), pointNdrag)
        while (len(splitting_regions) < count):
            cv2.imshow('Detect %d rectangles' % (count), img)
            k = cv2.waitKey(1) & 0xFF
            if k == 27:
                break
        cv2.destroyAllWindows()
        return splitting_regions

    def preview(self, image, pts=None, contours=None, mark_pts=True, rects=None, window_title='Preview'):
        '''Отрисовывает контуры и точки, показывает в отдельном окне результат
        РЕЗУЛЬТАТ ПОЛУЧАЕТСЯ ТОЛЬКО НА ЦВЕТНЫХ (BGR) ИЗОБРАЖЕНИЯХ'''
        try:
            img = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        except cv2.error:
            img = image
        if rects is not None:
            for r in rects:
                cv2.rectangle(img, (r[0], r[1]), (r[2], r[3]), (0, 255, 0), self.PREVIEW_LINE_THICKNESS)
        if contours is not None:
            cv2.drawContours(img, contours, -1, (0, 255, 0), self.PREVIEW_LINE_THICKNESS)
        if pts is not None:
            for i in range(len(pts)):
                p = tuple([int(j) for j in pts[i]])
                cv2.circle(img, p, self.PREVIEW_POINT_THICKNESS,
                           (0, 0, 255), -1)
                if mark_pts:
                    cv2.putText(img, str(i), p, cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,200), 8)
        cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_title, 800, 600)
        cv2.imshow(window_title, img)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()

    def get_roi(self, img, region):
        return img[region[1]:region[3], region[0]:region[2]]

    def roi_processing(self, src_img, regions):
        '''Возвращает массив данных, извлеченных из ответов на вопрос'''
        img = self.preprocessing_image(src_img)
        result = []
        self.preview(img, rects=regions)
        for i in range(len(regions)):
            reg = regions[i]
            roi = self.get_roi(img, reg)            
            result.append(self.is_filled(roi, invert=True))
        return result

    def is_filled(self, roi_image, mask=None, invert=False):
        '''Проверяет изображение на соответствие маске.
        Если маска не указана - проверяет на однородность цвета (белый)
        Допустимая погрешность задается в константе FILLING_THRESHOLD'''
        if invert:
            roi_image = cv2.bitwise_not(roi_image)
        filling_threshold = self.FILLING_THRESHOLD
        # создаем все возможные повороты маски если таковая присутствует
        if type(mask) == np.ndarray:
            rows, cols = roi_image.shape[:2]
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
            Ms = [cv2.getRotationMatrix2D(
                (cols / 2, rows / 2), i, 1) for i in range(0, 359, 90)]
            masks = [cv2.warpAffine(mask, m, (cols, rows)) for m in Ms]
            roi_images = [cv2.bitwise_xor(roi_image, mask) for mask in masks]
        # или ничего, оставляем исходное изображение
        else:
            roi_images = [roi_image]
        intensities = []
        filling_intensities = []
        for roi_image in roi_images:
            # подготовка изображения
            kernel = np.ones((7, 7), np.uint8)
            roi_image = cv2.morphologyEx(roi_image, cv2.MORPH_CLOSE, kernel)
            mean_intensity = np.mean(roi_image)
            filling_intensity = mean_intensity / 255
            intensities.append(filling_intensity >= filling_threshold)
            filling_intensities.append(filling_intensity)
        #print (filling_intensities)
        return any(intensities)

    ###
    # Методы, отвечающие за подготовку изображения,
    # а также детекцию стороны и ориентации изображения
    ###

    def detect_side(self):
        '''Определяем сторону листа по квадратику в нижнем правом углу'''
        _img = self.src_img
        img = self.preprocessing_image(_img)
        img, contours, hierarchy = cv2.findContours(
            img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        square_contours, _, _ = self.filter_contours(contours,
                                                     self.PAPER_SIDEBOX)
        if len(square_contours) == 1:
            xy, wh, a = cv2.minAreaRect(square_contours[0])
            M = cv2.getRotationMatrix2D(xy, a, 1)
            img = cv2.warpAffine(img, M, img.shape[::-1])
            minx = int(xy[0] - wh[0] / 2)
            maxx = int(xy[0] + wh[0] / 2)
            miny = int(xy[1] - wh[1] / 2)
            maxy = int(xy[1] + wh[1] / 2)
            roi = img[miny:maxy, minx:maxx]
            max_intensity = 0
            for mask_name in self.MASKS:
                if self.is_filled(
                        roi, self.SIDE_FILLING_THRESHOLD,
                        self.MASKS[mask_name]):
                    self._side = mask_name
                    break
            return bool(self._side)

    def find_corners(self, input_image):
        '''Находит угловые элементы на на листе'''
        img = self.preprocessing_image(input_image)
        img, contours, hierarchy = cv2.findContours(
            img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # находим на изображении контур листа. Это должен быть контур, в котором находятся другие элементы
        hierarchy = hierarchy[0]
        area = 0
        paper_index = -1
        for i in range(hierarchy.shape[0]):
            if hierarchy[i][3] == -1 and hierarchy[i][2] >= 0:
                c_area = cv2.contourArea(contours[i])
                if c_area > area:
                    paper_index = i
                    area = c_area
        if paper_index < 0:
            return []     
        paper_contours = contours[paper_index]
        # находим контуры внутри листа
        inner_contours = []
        for i in range(hierarchy.shape[0]):
            if hierarchy[i][3] == paper_index:
                inner_contours.append(contours[i])
        centroids = [self.get_contour_centroid(c) for c in inner_contours]      
        # находим BBox для контура листа и сортируем его углы в нужном порядке
        rect = cv2.minAreaRect(paper_contours)
        rect = cv2.boxPoints(rect)
        rect_centroid = self.get_contour_centroid(rect)
        box_pts = [pt for pt in rect]
        #print(box_pts)
        box_pts.sort(key=lambda x: np.arctan2(x[1]-rect_centroid[1], x[0]-rect_centroid[0]))
        # находим самые близкие к углам листа точки
        pt0 = sorted(centroids, key=lambda x: np.linalg.norm(x - box_pts[0]))[0]
        pt1 = sorted(centroids, key=lambda x: np.linalg.norm(x - box_pts[1]))[0]
        pt2 = sorted(centroids, key=lambda x: np.linalg.norm(x - box_pts[2]))[0]
        pt3 = sorted(centroids, key=lambda x: np.linalg.norm(x - box_pts[3]))[0]
        return [pt0, pt1, pt2, pt3]

    def warp_img(self, src_img, dst_img):
        src_pts = np.float32(self.find_corners(src_img))
        dst_pts = np.float32(self.find_corners(dst_img))
        self.preview(src_img, pts = src_pts)
        self.preview(dst_img, pts = dst_pts)
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        affined_img = cv2.warpPerspective(src_img, M, (self.example_img.shape[1], self.example_img.shape[0]))
        return affined_img

if __name__ == '__main__':
    r = [[
        2290,
        382,
        2349,
        441
      ],
      [
        2288,
        458,
        2347,
        517
      ],
      [
        2289,
        530,
        2348,
        589
      ],
      [
        2290,
        606,
        2349,
        665
      ],
      [
        2289,
        679,
        2348,
        738
      ],
      [
        2289,
        753,
        2348,
        812
      ],
      [
        2289,
        971,
        2348,
        1030
      ]]
    rec = ImageRecognizer(regions=r)
    rec.start_capturing()
