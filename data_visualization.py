import pandas
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.style as style
from textwrap import wrap
import common

con = sqlite3.connect('2rd stage\\zag.sqlite')

resp_data = pandas.read_sql('select * from respondents', con)
resp_count = resp_data.RespondentId.count()

dataset = pandas.read_sql('select * from quest_04', con)
title = common.get_JSON_item_by_attribute(table_name='Quest_05')['quest']
try:
	data = dataset[dataset.AnotherFlag == 0].groupby('AnswerText').RespondentId.count()
except AttributeError:
	data = dataset.groupby('AnswerText').RespondentId.count()
data = data.to_frame()
data['test'] = data.RespondentId / resp_count * 100

style.use('fivethirtyeight')
viz = data.plot(
    kind='barh', 
    y='test', 
    figsize=(8, 8), 
    legend=False,
    title=title)

viz.set_xlim(right=100)
viz.set_xticks([i for i in range (0, 101, 10)], minor=False)
viz.set_xticklabels(['{}%'.format(i) for i in range (0, 101, 10)])

viz.axhline(y=0, color='black', linewidth=1.5, alpha=0.7)
viz.axvline(x=0, color='black', linewidth=1.5, alpha=0.7)

viz.yaxis.label.set_visible(False)

labels=data.index
labels = [ '\n'.join(wrap(l, 40)) for l in labels ]
viz.set_yticklabels(labels)

viz.text(x = 1965.8, y = -7,
    s = ' ©DATAQUEST Source: National Center for Education Statistics',fontsize = 14, color = '#f0f0f0', backgroundcolor = 'grey')

plt.show()
# plt.savefig('%02d.png' % (i))