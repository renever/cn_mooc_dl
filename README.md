cn_mooc_dl
==========

1. 中国大学 MOOC（`icourse163.org`）视频下载
2. 清华学堂在线（`xuetangx.com`）视频下载
3. 网易云课堂（`study.163.com`）视频下载

####中国大学 MOOC（`icourse163.org`）：
    python icourse163_dl.py  -u <username@xxx.xxx> -p <password>  "url"

* 其中 url 是打开课程页面后，浏览器地址栏‘#’之前部分。
以“国防科大高等数学（一）”为例，打开课程后浏览器地址栏显示为：
`http://www.icourse163.org/learn/nudt-9004#/learn/announce`
则 url 为 `http://www.icourse163.org/learn/nudt-9004`

* 网易流量时快时慢，时有时无。可以运行两遍，之前没下完的可断线续传。

####清华学堂在线（`xuetangx.com`）：    
    python xuetangx_dl.py  -u <username@xxx.xxx> -p <password>  "url"
    
* 其中 url 是课程课件页面的浏览器地址，比如：
`http://www.xuetangx.com/courses/HITx/GO90300700/2014_T2/courseware/`

####网易云课堂（`study.163.com`）：
    python study163_dl.py "url"

* 网易云课堂不必登录。
其中 url 是课程列表页面浏览器地址，比如:
`http://study.163.com/course/introduction/334013.htm`



    --path 用于指定保存文件夹， --overwrite 指定是否覆盖
