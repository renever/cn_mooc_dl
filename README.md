cn_mooc_dl
==========

1. 中国大学 MOOC（`icourse163.org`）视频下载
2. 清华学堂在线（`xuetangx.com`）视频下载
3. 网易云课堂（`study.163.com`）视频下载
4. 网易云课堂计算机专业课程（`mooc.study.163.com`）视频下载

####测试环境：   `PYTHON 2.7； WIN 7`
####依赖包： `requests， beautifulsoup4`
	pip install requests
	pip install beautifulsoup4
或者在代码目录下
	
	pip install -r requirements.txt 


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
* 云课堂新增专栏“计算机专业课程”那一部分（mooc.study.163.com）有点特殊，具体看下面。
* 收费课程下不了。
* 网易云课堂不必登录。其中 url 是课程列表页面浏览器地址，比如:
`http://study.163.com/course/introduction/334013.htm`
* 不能续传。

 
####云课堂计算机专业课程（`mooc.study.163.com`）： 
    python icourse163_dl.py  -u <username@xxx.xxx> -p <password>  "url" 
* 云课堂新增专栏“计算机专业课程”，虽然挂在云课堂页面上，但是里面的结构是和“中国大学 MOOC”一样的。所以要用 `icourse163_dl.py` 来下载。
* 其中 url 类似这样： `http://mooc.study.163.com/learn/ZJU-1000002014`


#####--path 用于指定保存文件夹， --overwrite 指定是否覆盖


matthieu.lin@gmail.com