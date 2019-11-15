import cv2
import numpy as np
import math
import os
import copy


class SideRecognizeError(Exception):
    def __init__(self):
        super().__init__(self, "Can't recognize the side")


class ImageRecognizer:
    FIELD_THRESHOLD = 10

    MASKS_PATH = 'side_masks\\'
    MASKS = {}

    def __init__(self, src_path=None, example_path=None, regions=None, field_size=None, fill_threshold=None):
        if src_path:
            self.src_img = self.open_image(src_path)
        if example_path:
            self.example_img = self.open_image(example_path)
        self.regions = regions
        self.field_size = field_size
        self.FILLING_THRESHOLD = fill_threshold

    def open_image(self, path):
        path = os.path.relpath(path)
        path = path.replace('\\', '/')
        img = cv2.imread(path)
        try:
            print(img.shape)
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
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        while(cap.isOpened()):
            k = cv2.waitKey(33)
            ret, frame = cap.read()
            pts = self.find_paper_corners(frame)
            self.preview(frame, pts=pts,
                         window_title='Esc for quit, Space for commit',
                         waitkeys=False)
            if k == 27:  # Esc
                succeed = False
                break
            elif k == 32:  # Space
                succeed = True
                self.set_src_img2(frame)
                break
        cap.release()
        cv2.destroyAllWindows()
        return succeed

    def get_values(self):
        #img = self.find_paper(self.src_img)
        img = self.warp_image(self.src_img, self.example_img)
        values = self.find_checked_fields(img, self.regions)
        return values

    def get_contour_centroid(self, c):
        try:
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            return (cX, cY)
        except ZeroDivisionError:
            return None

    def crop(self, image, size):
        end_y, end_x = image.shape[:2]
        return image[size:end_y - size, size:end_x - size]

    def pts2contour(self, pts):
        return np.asarray([[pt] for pt in pts])

    def image_prepare_adaptive(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.GaussianBlur(img, (5, 5), 0)
        img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 11, 3)
        return img

    def image_prepare_simple(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.GaussianBlur(img, (3, 3), 0)
        ret, img = cv2.threshold(
            img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
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

    def preview(self, image, pts=None, contours=None, mark_pts=True, rects=None, window_title='Preview', waitkeys=True):
        '''Отрисовывает контуры и точки, показывает в отдельном окне результат
        РЕЗУЛЬТАТ ПОЛУЧАЕТСЯ ТОЛЬКО НА ЦВЕТНЫХ (BGR) ИЗОБРАЖЕНИЯХ'''
        lineThikness = int(image.shape[0] * 0.001)
        pointSize = int(image.shape[0] * 0.005)
        fontSize = int(image.shape[0] * 0.0015)
        ratio = image.shape[1] / image.shape[0]
        try:
            img = cv2.cvtColor(image.copy(), cv2.COLOR_GRAY2BGR)
        except cv2.error:
            img = image.copy()
        if rects is not None:
            for r in rects:
                cv2.rectangle(img, (r[0], r[1]),
                              (r[2], r[3]), (0, 255, 0), lineThikness)
        if contours is not None:
            cv2.drawContours(img, contours, -1, (0, 255, 0), lineThikness)
        if pts is not None:
            for i in range(len(pts)):
                p = tuple([int(j) for j in pts[i]])
                cv2.circle(img, p, pointSize,
                           (0, 0, 255), -1)
                if mark_pts:
                    cv2.putText(img, str(i), p, cv2.FONT_HERSHEY_SIMPLEX,
                                fontSize, (255, 0, 0), lineThikness)
        cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_title, (int(ratio * 600), 600))
        cv2.imshow(window_title, img)
        if waitkeys:
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    def get_roi(self, img, region):
        return img[region[0][1]:region[1][1], region[0][0]:region[1][0]]

    def roi_processing(self, img, regions):
        '''Возвращает массив данных, извлеченных из ответов на вопрос'''
        intensities = []
        for i in range(len(regions)):
            reg = regions[i]
            roi = self.get_roi(img, reg)
            intensities.append(self.filling_intensity(roi))
        result = self.areChecked(intensities)
        return result

    def areChecked(self, intensities):
        # РЕАЛИЗОВАТЬ ТОЧНОЕ ВЫЧИСЛЕНИЕ СРЕДНЕГО ЗНАЧЕНИЯ
        return [i > self.FILLING_THRESHOLD for i in intensities]

    def filling_intensity(self, roi_image, mask=None):
        '''Проверяет изображение на соответствие маске.
        Если маска не указана - проверяет на однородность цвета (белый)
        Допустимая погрешность задается в константе FILLING_THRESHOLD'''
        # подготовка изображения
        try:
            kernel = np.ones((7, 7), np.uint8)
            roi_image = cv2.dilate(roi_image, kernel, iterations=1)
            roi_image = cv2.bitwise_not(roi_image)
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
            filling_intensities = []
            for roi_image in roi_images:
                mean_intensity = np.mean(roi_image)
                filling_intensity = mean_intensity / 2.55
                filling_intensities.append(filling_intensity)
            return max(filling_intensities)
        except:
            return 0

    ###
    # Методы, отвечающие за подготовку изображения,
    # а также детекцию стороны и ориентации изображения
    ###

    def detect_side(self):
        '''Определяем сторону листа по квадратику в нижнем правом углу'''
        _img = self.src_img
        img = self.image_prepare_simple(_img)
        contours, hierarchy = cv2.findContours(
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
                if self.filling_intensity(
                        roi, self.SIDE_FILLING_THRESHOLD,
                        self.MASKS[mask_name]):
                    self._side = mask_name
                    break
            return bool(self._side)

    def isRect(self, cnt):
        validThresh = (self.field_size - self.FIELD_THRESHOLD)**2 < cv2.contourArea(
            cnt) < (self.field_size + self.FIELD_THRESHOLD)**2
        bbox = cv2.boundingRect(cnt)
        validRatio = 0.5 < bbox[2] / bbox[3] < 2
        return validRatio and validThresh

    def find_paper_corners(self, input_image):
        '''Находит углы листа'''
        img = self.image_prepare_simple(input_image)
        contours, hierarchy = cv2.findContours(
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
        paper_contour = contours[paper_index]
        # находим контур листа и сортируем его углы в нужном порядке
        epsilon = 0.1 * cv2.arcLength(paper_contour, True)
        approx_rect = cv2.approxPolyDP(paper_contour, epsilon, True)
        bbox_rect = cv2.minAreaRect(paper_contour)
        bbox_rect_pts = cv2.boxPoints(bbox_rect)
        bbox_rect_centroid = self.get_contour_centroid(bbox_rect_pts)
        approx_rect_pts = [(i[0][0], i[0][1]) for i in approx_rect]
        approx_rect_pts.sort(key=lambda x: np.arctan2(
            x[1] - bbox_rect_centroid[1], x[0] - bbox_rect_centroid[0]))
        return approx_rect_pts

    def find_reference_pts(self, input_image):
        img = self.image_prepare_adaptive(input_image)
        contours, hierarchy = cv2.findContours(
            img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        hierarchy = np.squeeze(hierarchy)
        height, width = img.shape[:2]
        parent_index = [i for i in range(
            len(hierarchy)) if hierarchy[i][-1] == -1][0]
        contours = [contours[i] for i in range(
            len(hierarchy)) if hierarchy[i][-1] == parent_index]
        contours = list(filter(self.isRect, contours))
        centroids = [self.get_contour_centroid(c) for c in contours]
        centroids = [c for c in centroids if c]
        # находим самые близкие к углам листа точки
        # Порядок точек:
        # 0  1
        # 3  2
        pt0 = sorted(centroids, key=lambda x: np.linalg.norm(
            x - np.float32((0, 0))))[0]
        pt1 = sorted(centroids, key=lambda x: np.linalg.norm(
            x - np.float32((img.shape[1], 0))))[0]
        pt2 = sorted(centroids, key=lambda x: np.linalg.norm(
            x - np.float32((img.shape[1], img.shape[0]))))[0]
        pt3 = sorted(centroids, key=lambda x: np.linalg.norm(
            x - np.float32((0, img.shape[0]))))[0]
        result = [pt0, pt1, pt3]
        return result

    def find_paper(self, src_img):
        src_pts = np.float32(self.find_paper_corners(src_img))
        height, width = src_img.shape[:2]
        dst_pts = np.float32(
            [(0, 0), (width, 0), (width, height), (0, height)])
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        affined_img = cv2.warpPerspective(src_img, M, (width, height))
        return affined_img

    def warp_image(self, src_img, dst_img):
        src_pts = np.float32(self.find_reference_pts(src_img))
        #self.preview(src_img, pts=src_pts)
        dst_pts = np.float32(self.find_reference_pts(dst_img))
        rows, cols = dst_img.shape[:2]
        M = cv2.getAffineTransform(src_pts, dst_pts)
        affined_img = cv2.warpAffine(src_img, M, (cols, rows))
        return affined_img

    def feature_matching(self, src_img, dst_img):
        orb = cv2.ORB_create()
        kp1, des1 = orb.detectAndCompute(src_img, None)
        kp2, des2 = orb.detectAndCompute(dst_img, None)
        bf = cv2.BFMatcher(cv2.NORM_HAMMING2, crossCheck=True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)
        img3 = cv2.drawMatches(src_img, kp1, dst_img, kp2,
                               matches[:10], outImg=None, flags=2)
        self.preview(img3, waitkeys=True)

    def find_checked_fields(self, src_img, question_regions):
        img = self.image_prepare_simple(src_img)
        contours, hierarchy = cv2.findContours(
            img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        height, width = img.shape[:2]
        contours = list(filter(self.isRect, contours))
        centroids = [self.get_contour_centroid(i) for i in contours]
        question_correct_regions = {}
        for question, region in question_regions.items():
            region_center = np.median(region, axis=0)
            diff_vecs = [np.float32(np.float32(c)-region_center) for c in centroids]
            min_diff_vec = min(diff_vecs, key=lambda x: np.linalg.norm(x))
            corrected_region = region + min_diff_vec
            question_correct_regions[question] = corrected_region.astype(int)
        question_intesities = {}
        for question, region in question_correct_regions.items():
            roi = self.get_roi(img, region)
            region_intensity = self.filling_intensity(roi)
            question_intesities[question] = region_intensity

        timg = src_img.copy()  
        checked_questions = []
        for question in question_correct_regions:
            reg = question_correct_regions[question]
            if question_intesities[question] > self.FILLING_THRESHOLD:
                checked_questions.append(question)
                timg = cv2.rectangle(timg, tuple(reg[0]), tuple(
                    reg[1]), (0, 255, 0), 2)
            else:
                timg = cv2.rectangle(timg, tuple(reg[0]), tuple(
                    reg[1]), (0, 0, 255), 2)        
        self.preview(timg, waitkeys=True)
        return checked_questions


if __name__ == '__main__':
    with open('z.trv', 'r') as file:
        settings = json.load(file)['IR_SETTINGS']
    rec = ImageRecognizer()
    i1 = rec.start_capturing()
    i2 = rec.open_image('tr_exampleA.jpg')
    i1 = rec.find_paper(i1)
    i = rec.warp_image(i1, i2)
    rec.find_checked_fields(i, settings['Regions'])

    #rec.preview(i, pts, waitkeys=True)
