cn_mooc_dl
==========

中国大学 MOOC（icourse163.org）视频下载
清华学堂在线（xuetangx.com）视频下载

格式：

python icourse163_dl.py  -u username@xxx.xxx -p password  "url"
python xuetangx_dl.py -u username@xxx.xxx -p password  "url"

关于 icourse163.org:
其中 url 是打开课程页面后，浏览器地址栏‘#’之前部分,以“国防科大高等数学（一）”为例，打开课程后浏览器地址栏显示为：
http://www.icourse163.org/learn/nudt-9004#/learn/announce
则 url 为 http://www.icourse163.org/learn/nudt-9004

关于 xuetangx.com:
其中 url 是课程课件页面的浏览器地址，比如
http://www.xuetangx.com/courses/HITx/GO90300700/2014_T2/courseware/


另有可选参数 --path 用于指定保存文件夹， --overwrite 指定是否覆盖
