import os
import sys
import time

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QApplication, QDialog

from mediainfo import get_media_info
from rename import get_video_info
from screenshot import extract_complex_keyframes, upload_screenshot, upload_free_screenshot
from tool import update_settings, get_settings, get_file_path, rename_file_with_same_extension, \
    get_folder_path, check_path_and_find_video, rename_directory, create_torrent, load_names, chinese_name_to_pinyin, \
    get_video_files
from ui.mainwindow import Ui_Mainwindow
from ui.settings import Ui_Settings


def starui():
    app = QApplication(sys.argv)
    myMainwindow = mainwindow()
    myico = QIcon("static/apr-bjd.ico")
    myMainwindow.setWindowIcon(myico)
    myMainwindow.show()
    sys.exit(app.exec())


class mainwindow(QMainWindow, Ui_Mainwindow):
    def __init__(self):
        super().__init__()
        self.upload_cover_thread = None
        self.upload_free_cover_thread = None
        self.setupUi(self)  # 设置界面

        self.get_pt_gen_thread = None
        self.get_pt_gen_for_name_thread = None
        self.upload_picture_thread0 = None
        self.upload_picture_thread1 = None
        self.upload_picture_thread2 = None
        self.upload_picture_thread3 = None
        self.upload_picture_thread4 = None
        self.upload_free_picture_thread0 = None
        self.upload_free_picture_thread1 = None
        self.upload_free_picture_thread2 = None
        self.upload_free_picture_thread3 = None
        self.upload_free_picture_thread4 = None
        self.make_torrent_thread = None

        # 初始化
        self.videoPath.setDragEnabled(True)
        self.introBrowser.setText("")
        self.pictureUrlBrowser.setText("")
        self.mediainfoBrowser.setText("")
        self.debugBrowser.setText("")
        self.initialize_team_combobox()
        self.initialize_source_combobox()
        self.initialize_type_combobox()

        # 绑定点击信号和槽函数
        self.actionsettings.triggered.connect(self.settingsClicked)
        self.getPictureButton.clicked.connect(self.getPictureButtonClicked)
        self.uploadCoverButton.clicked.connect(self.uploadCoverButtonClicked)
        self.selectVideoFolderButton.clicked.connect(self.selectVideoFolderButtonClicked)
        self.selectCoverFolderButton.clicked.connect(self.selectCoverFolderButtonClicked)
        self.getMediaInfoButton.clicked.connect(self.getMediaInfoButtonClicked)
        self.getNameButton.clicked.connect(self.getNameButtonClicked)
        self.startButton.clicked.connect(self.startButtonClicked)
        self.makeTorrentButton.clicked.connect(self.makeTorrentButtonClicked)

        self.debugBrowser.append("程序初始化成功，使用前请查看设置中的说明")

    def initialize_team_combobox(self):
        team_names = load_names('static/team.json', 'team')
        for name in team_names:
            self.team.addItem(name)

    def initialize_source_combobox(self):
        source_names = load_names('static/source.json', 'source')
        for name in source_names:
            self.source.addItem(name)

    def initialize_type_combobox(self):
        type_names = load_names('static/type.json', 'type')
        for name in type_names:
            self.type.addItem(name)

    def startButtonClicked(self):
        self.getNameButtonClicked()
        QApplication.processEvents()  # 处理所有挂起的事件，更新页面
        time.sleep(0)  # 等待 0 毫秒
        self.getPictureButtonClicked()
        QApplication.processEvents()  # 再次处理事件
        time.sleep(0)  # 等待 2000 毫秒
        self.uploadCoverButtonClicked()
        QApplication.processEvents()  # 再次处理事件
        time.sleep(2)  # 等待 2000 毫秒
        self.getMediaInfoButtonClicked()
        QApplication.processEvents()  # 处理事件
        time.sleep(2)  # 等待 2000 毫秒
        self.makeTorrentButtonClicked()
        QApplication.processEvents()  # 处理事件

    def settingsClicked(self):  # click对应的槽函数
        self.mySettings = settings()
        self.mySettings.getSettings()
        myico = QIcon("static/apr-bjd.ico")
        self.mySettings.setWindowIcon(myico)
        self.mySettings.show()  # 加上self避免页面一闪而过

    def uploadCoverButtonClicked(self):
        cover_path = self.coverPath.text()
        if cover_path:
            self.debugBrowser.append("上传封面" + cover_path)
            figureBedPath = get_settings("figureBedPath")  # 图床地址
            figureBedToken = get_settings("figureBedToken")  # 图床Token
            self.debugBrowser.append("参数获取成功，开始执行截图函数")
            if figureBedPath == "https://img.agsvpt.com/api/upload/" or figureBedPath == "http://img.agsvpt.com/api/upload/":

                self.upload_cover_thread = UploadPictureThread(figureBedPath, figureBedToken, cover_path, True)
                self.upload_cover_thread.result_signal.connect(self.handleUploadPictureResult)  # 连接信号
                self.upload_cover_thread.start()  # 启动线程
                print("上传图床线程启动")
                self.debugBrowser.append("上传图床线程启动")
            else:
                self.upload_free_cover_thread = UploadFreePictureThread(figureBedPath, figureBedToken, cover_path, True)
                self.upload_free_cover_thread.result_signal.connect(self.handleUploadFreePictureResult)  # 连接信号
                self.upload_free_cover_thread.start()  # 启动线程

                print("上传图床线程启动")
                self.debugBrowser.append("上传图床线程启动")

    def getPictureButtonClicked(self):
        self.pictureUrlBrowser.setText("")
        isVideoPath, videoPath = check_path_and_find_video(self.videoPath.text())  # 视频资源的路径

        if isVideoPath == 1 or isVideoPath == 2:
            self.debugBrowser.append("获取视频" + videoPath + "的截图")
            screenshotPath = get_settings("screenshotPath")  # 截图储存路径
            figureBedPath = get_settings("figureBedPath")  # 图床地址
            figureBedToken = get_settings("figureBedToken")  # 图床Token
            screenshotNumber = int(get_settings("screenshotNumber"))
            screenshotThreshold = float(get_settings("screenshotThreshold"))
            screenshotStart = float(get_settings("screenshotStart"))
            screenshotEnd = float(get_settings("screenshotEnd"))
            autoUploadScreenshot = bool(get_settings("autoUploadScreenshot"))
            self.debugBrowser.append("参数获取成功，开始执行截图函数")

            screenshot_success, res = extract_complex_keyframes(videoPath, screenshotPath, screenshotNumber,
                                                                screenshotThreshold, screenshotStart,
                                                                screenshotEnd, min_interval_pct=0.01)
            print("成功获取截图函数的返回值")
            self.debugBrowser.append("成功获取截图函数的返回值")
            if screenshot_success:
                # 判断是否需要上传图床
                self.debugBrowser.append("成功获取截图：" + str(res))
                if autoUploadScreenshot:
                    self.debugBrowser.append("开始自动上传截图到图床" + figureBedPath)
                    self.pictureUrlBrowser.setText("")
                    if figureBedPath == "https://img.agsvpt.com/api/upload/" or figureBedPath == "http://img.agsvpt.com/api/upload/":
                        if len(res) > 0:
                            self.upload_picture_thread0 = UploadPictureThread(figureBedPath, figureBedToken, res[0],
                                                                              False)
                            self.upload_picture_thread0.result_signal.connect(self.handleUploadPictureResult)  # 连接信号
                            self.upload_picture_thread0.start()  # 启动线程
                        if len(res) > 1:
                            self.upload_picture_thread1 = UploadPictureThread(figureBedPath, figureBedToken, res[1],
                                                                              False)
                            self.upload_picture_thread1.result_signal.connect(self.handleUploadPictureResult)  # 连接信号
                            self.upload_picture_thread1.start()  # 启动线程
                        if len(res) > 2:
                            self.upload_picture_thread2 = UploadPictureThread(figureBedPath, figureBedToken, res[2],
                                                                              False)
                            self.upload_picture_thread2.result_signal.connect(self.handleUploadPictureResult)  # 连接信号
                            self.upload_picture_thread2.start()  # 启动线程
                        if len(res) > 3:
                            self.upload_picture_thread3 = UploadPictureThread(figureBedPath, figureBedToken, res[3],
                                                                              False)
                            self.upload_picture_thread3.result_signal.connect(self.handleUploadPictureResult)  # 连接信号
                            self.upload_picture_thread3.start()  # 启动线程
                        if len(res) > 4:
                            self.upload_picture_thread4 = UploadPictureThread(figureBedPath, figureBedToken, res[4],
                                                                              False)
                            self.upload_picture_thread4.result_signal.connect(self.handleUploadPictureResult)  # 连接信号
                            self.upload_picture_thread4.start()  # 启动线程
                        print("上传图床线程启动")
                        self.debugBrowser.append("上传图床线程启动")
                    else:
                        if len(res) > 0:
                            self.upload_free_picture_thread0 = UploadFreePictureThread(figureBedPath, figureBedToken,
                                                                                       res[0], False)
                            self.upload_free_picture_thread0.result_signal.connect(
                                self.handleUploadFreePictureResult)  # 连接信号
                            self.upload_free_picture_thread0.start()  # 启动线程
                        if len(res) > 1:
                            self.upload_free_picture_thread1 = UploadFreePictureThread(figureBedPath, figureBedToken,
                                                                                       res[1], False)
                            self.upload_free_picture_thread1.result_signal.connect(
                                self.handleUploadFreePictureResult)  # 连接信号
                            self.upload_free_picture_thread1.start()  # 启动线程
                        if len(res) > 2:
                            self.upload_free_picture_thread2 = UploadFreePictureThread(figureBedPath, figureBedToken,
                                                                                       res[2], False)
                            self.upload_free_picture_thread2.result_signal.connect(
                                self.handleUploadFreePictureResult)  # 连接信号
                            self.upload_free_picture_thread2.start()  # 启动线程
                        if len(res) > 3:
                            self.upload_free_picture_thread3 = UploadFreePictureThread(figureBedPath, figureBedToken,
                                                                                       res[3], False)
                            self.upload_free_picture_thread3.result_signal.connect(
                                self.handleUploadFreePictureResult)  # 连接信号
                            self.upload_free_picture_thread3.start()  # 启动线程
                        if len(res) > 4:
                            self.upload_free_picture_thread4 = UploadFreePictureThread(figureBedPath, figureBedToken,
                                                                                       res[4], False)
                            self.upload_free_picture_thread4.result_signal.connect(
                                self.handleUploadFreePictureResult)  # 连接信号
                            self.upload_free_picture_thread4.start()  # 启动线程
                        print("上传图床线程启动")
                        self.debugBrowser.append("上传图床线程启动")
                else:
                    self.debugBrowser.append("未选择自动上传图床功能，图片已储存在本地")
                    output = ""
                    for r in res:
                        output += r
                        output += '\n'
                    self.pictureUrlBrowser.setText(output)
            else:
                self.debugBrowser.append("截图失败" + str(res))
        else:
            self.debugBrowser.append("您的视频文件路径有误")

    def handleUploadPictureResult(self, upload_success, api_response, screenshot_path, is_cover):
        # 这个函数用于处理上传的结果，它将在主线程中被调用
        # 更新UI，显示上传结果等
        print("接受到线程请求的结果")
        self.debugBrowser.append("接受到线程请求的结果")
        if upload_success:
            if api_response.get("statusCode", "") == "200":
                pasteScreenshotUrl = bool(get_settings("pasteScreenshotUrl"))
                deleteScreenshot = bool(get_settings("deleteScreenshot"))
                bbsurl = str(api_response.get("bbsurl", ""))
                self.pictureUrlBrowser.append(bbsurl)
                if pasteScreenshotUrl:
                    if is_cover:
                        temp = self.introBrowser.toPlainText()
                        temp = bbsurl + '\n' + temp
                        self.introBrowser.setText(temp)
                        self.debugBrowser.append("成功将封面链接粘贴到简介前")
                    else:
                        self.introBrowser.append(bbsurl)
                        self.debugBrowser.append("成功将图片链接粘贴到简介后")
                if deleteScreenshot:
                    if os.path.exists(screenshot_path):
                        # 删除文件
                        os.remove(screenshot_path)
                        print(f"文件 {screenshot_path} 已被删除。")
                        self.debugBrowser.append(f"文件 {screenshot_path} 已被删除。")
                    else:
                        print(f"文件 {screenshot_path} 不存在。")
                        self.debugBrowser.append(f"文件 {screenshot_path} 不存在。")
            else:
                if api_response.get("statusCode", "") == "":
                    self.debugBrowser.append("未接受到图床的任何响应" + '\n')
                else:
                    self.debugBrowser.append(str(api_response) + '\n')

        else:
            self.debugBrowser.append("图床响应不是有效的JSON格式")

    def handleUploadFreePictureResult(self, upload_success, api_response, screenshot_path, is_cover):
        # 这个函数用于处理上传的结果，它将在主线程中被调用
        # 更新UI，显示上传结果等
        print("接受到线程请求的结果")
        self.debugBrowser.append("接受到线程请求的结果")
        if upload_success:
            self.pictureUrlBrowser.append(api_response)
            pasteScreenshotUrl = bool(get_settings("pasteScreenshotUrl"))
            deleteScreenshot = bool(get_settings("deleteScreenshot"))
            if pasteScreenshotUrl:
                if is_cover:
                    temp = self.introBrowser.toPlainText()
                    temp = api_response + '\n' + temp
                    self.introBrowser.setText(temp)
                    self.debugBrowser.append("成功将封面链接粘贴到简介前")
                else:
                    self.introBrowser.append(api_response)
                    self.debugBrowser.append("成功将图片链接粘贴到简介后")
            if deleteScreenshot:
                if os.path.exists(screenshot_path):
                    # 删除文件
                    os.remove(screenshot_path)
                    print(f"文件 {screenshot_path} 已被删除。")
                    self.debugBrowser.append(f"文件 {screenshot_path} 已被删除。")
                else:
                    print(f"文件 {screenshot_path} 不存在。")
                    self.debugBrowser.append(f"文件 {screenshot_path} 不存在。")
        else:
            self.debugBrowser.append("图床响应无效：" + api_response)

    def selectCoverFolderButtonClicked(self):
        path = get_file_path()
        self.coverPath.setText(path)

    def selectVideoFolderButtonClicked(self):
        path = get_folder_path()
        self.videoPath.setText(path)

    def getMediaInfoButtonClicked(self):
        self.mediainfoBrowser.setText("")
        isVideoPath, videoPath = check_path_and_find_video(self.videoPath.text())  # 视频资源的路径
        if isVideoPath == 1 or isVideoPath == 2:
            get_media_info_success, mediainfo = get_media_info(videoPath)
            if get_media_info_success:
                self.mediainfoBrowser.setText(mediainfo)
                self.mediainfoBrowser.append('\n')
                self.debugBrowser.append("成功获取到MediaInfo")
            else:
                self.debugBrowser.append(mediainfo)
        else:
            self.debugBrowser.append("您的视频文件路径有误")

    def getNameButtonClicked(self):

        first_chinese_name = self.chineseNameEdit.text()
        if first_chinese_name:

            print('获取中文名成功：' + first_chinese_name)
            self.debugBrowser.append('获取中文名成功：' + first_chinese_name)
            first_english_name = chinese_name_to_pinyin(first_chinese_name)
            year = self.yearEdit.text()
            season = self.seasonBox.text()
            if len(season) < 2:
                season = '0'+season
            width = ""
            format = ""
            hdr_format = ""
            commercial_name = ""
            channel_layout = ""
            type = ""
            category = ""
            rename_file = get_settings("renameFile")
            isVideoPath, videoPath = check_path_and_find_video(self.videoPath.text())
            get_video_info_success, output = get_video_info(videoPath)
            print(get_video_info_success, output)
            if isVideoPath == 2:

                get_video_files_success, video_files = get_video_files(self.videoPath.text())
                print(video_files)
                print("获取到关键参数：" + str(output))
                self.debugBrowser.append("获取到关键参数：" + str(output))
                if get_video_info_success:
                    width = output[0]
                    format = output[1]
                    hdr_format = output[2]
                    commercial_name = output[3]
                    channel_layout = output[4]
                source = self.source.currentText()
                team = self.team.currentText()
                print("关键参数赋值成功")
                self.debugBrowser.append("关键参数赋值成功")
                type += self.type.currentText()
                if self.checkBox_0.isChecked():
                    category += '剧情 '
                if self.checkBox_1.isChecked():
                    category += '爱情 '
                if self.checkBox_2.isChecked():
                    category += '喜剧 '
                if self.checkBox_3.isChecked():
                    category += '甜虐 '
                if self.checkBox_4.isChecked():
                    category += '甜宠 '
                if self.checkBox_5.isChecked():
                    category += '恐怖 '
                if self.checkBox_6.isChecked():
                    category += '动作 '
                if self.checkBox_7.isChecked():
                    category += '穿越 '
                if self.checkBox_8.isChecked():
                    category += '重生 '
                if self.checkBox_9.isChecked():
                    category += '逆袭 '
                if self.checkBox_10.isChecked():
                    category += '科幻 '
                if self.checkBox_11.isChecked():
                    category += '武侠 '
                if self.checkBox_12.isChecked():
                    category += '都市 '
                if self.checkBox_13.isChecked():
                    category += '古装 '
                print('类型为：' + category)
                self.debugBrowser.append('类型为：' + category)
                mainTitle = first_english_name + ' ' + year + ' S' + season + ' ' + width + ' ' + source + ' ' + format + ' ' + hdr_format + ' ' + commercial_name + '' + channel_layout + '-' + team
                mainTitle = mainTitle.replace('  ', ' ')
                print(mainTitle)
                secondTitle = (first_chinese_name + ' | 全' + str(
                    len(video_files)) + '集 | ' + year + '年 | ' + type + ' | 类型：' + category)
                print("SecondTitle" + secondTitle)
                # NPC我要跟你谈恋爱 | 全95集 | 2023年 | 网络收费短剧 | 类型：剧集 爱情
                fileName = (
                        first_chinese_name + '.' + first_english_name + '.' + year + '.' + ' S' + season + 'E??' + '.' + width + '.' + source + '.' +
                        format + '.' + hdr_format + '.' + commercial_name + '' + channel_layout + '-' + team)
                fileName = fileName.replace(' – ', '.')
                fileName = fileName.replace(': ', '.')
                fileName = fileName.replace(' ', '.')
                fileName = fileName.replace('..', '.')
                print("FileName" + fileName)
                self.mainTitleBrowser.setText(mainTitle)
                self.secondTitleBrowser.setText(secondTitle)
                self.fileNameBrowser.setText(fileName)
                if rename_file:
                    print("对文件重新命名")
                    self.debugBrowser.append("开始对文件重新命名")
                    i = 1
                    for video_file in video_files:
                        e = str(i)
                        while len(e) < len(str(len(video_files))):
                            e = '0' + e
                        rename_file_success, output = rename_file_with_same_extension(video_file, fileName.replace('??', e))

                        if rename_file_success:
                            self.videoPath.setText(output)
                            videoPath = output
                            self.debugBrowser.append("视频成功重新命名为：" + videoPath)
                        else:
                            self.debugBrowser.append("重命名失败：" + output)
                        i += 1

                    print("对文件夹重新命名")
                    self.debugBrowser.append("开始对文件夹重新命名")
                    rename_directory_success, output = rename_directory(os.path.dirname(videoPath), fileName.replace('E??', ''))
                    if rename_directory_success:
                        self.videoPath.setText(output)
                        videoPath = output
                        self.debugBrowser.append("视频地址成功重新命名为：" + videoPath)
                    else:
                        self.debugBrowser.append("重命名失败：" + output)
            else:
                self.debugBrowser.append("您的视频文件路径有误")
        else:
            self.debugBrowser.append('获取中文名失败')


    def makeTorrentButtonClicked(self):
        isVideoPath, videoPath = check_path_and_find_video(self.videoPath.text())  # 视频资源的路径
        if isVideoPath == 1 or isVideoPath == 2:
            torrent_path = str(get_settings("torrentPath"))
            folder_path = os.path.dirname(videoPath)
            self.debugBrowser.append("开始将" + folder_path + "制作种子，储存在" + torrent_path)
            self.make_torrent_thread = MakeTorrentThread(folder_path, torrent_path)
            self.make_torrent_thread.result_signal.connect(self.handleMakeTorrentResult)  # 连接信号
            self.make_torrent_thread.start()  # 启动线程
            self.debugBrowser.append("制作种子线程启动成功")
        else:
            self.debugBrowser.append("制作种子失败：" + videoPath)

    def handleMakeTorrentResult(self, get_success, response):
        if get_success:
            self.debugBrowser.append("成功制作种子：" + response)
        else:
            self.debugBrowser.append("制作种子失败：" + response)


class settings(QDialog, Ui_Settings):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 设置界面

        # 绑定点击信号和槽函数
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.cancelButton.clicked.connect(self.cancelButtonClicked)
        self.selectScreenshotPathButton.clicked.connect(self.selectScreenshotPathButtonClicked)
        self.selectTorrentPathButton.clicked.connect(self.selectTorrentPathButtonClicked)

    def saveButtonClicked(self):
        self.updateSettings()
        self.close()

    def cancelButtonClicked(self):
        self.close()

    def selectScreenshotPathButtonClicked(self):
        path = get_folder_path()
        if path != '':
            self.screenshotPath.setText(path)

    def selectTorrentPathButtonClicked(self):
        path = get_folder_path()
        if path != '':
            self.torrentPath.setText(path)

    def getSettings(self):
        self.screenshotPath.setText(str(get_settings("screenshotPath")))
        self.torrentPath.setText(str(get_settings("torrentPath")))
        self.figureBedPath.setText(get_settings("figureBedPath"))
        self.figureBedToken.setText(get_settings("figureBedToken"))
        self.screenshotNumber.setValue(int(get_settings("screenshotNumber")))
        self.screenshotThreshold.setValue(float(get_settings("screenshotThreshold")))
        self.screenshotStart.setValue(float(get_settings("screenshotStart")))
        self.screenshotEnd.setValue(float(get_settings("screenshotEnd")))
        self.autoUploadScreenshot.setChecked(bool(get_settings("autoUploadScreenshot")))
        self.pasteScreenshotUrl.setChecked(bool(get_settings("pasteScreenshotUrl")))
        self.deleteScreenshot.setChecked(bool(get_settings("deleteScreenshot")))
        self.makeDir.setChecked(bool(get_settings("makeDir")))
        self.renameFile.setChecked(bool(get_settings("renameFile")))

    def updateSettings(self):
        update_settings("screenshotPath", self.screenshotPath.text())
        update_settings("torrentPath", self.torrentPath.text())
        update_settings("figureBedPath", self.figureBedPath.text())
        update_settings("figureBedToken", self.figureBedToken.text())
        update_settings("screenshotNumber", str(self.screenshotNumber.text()))
        update_settings("screenshotThreshold", str(self.screenshotThreshold.text()))
        update_settings("screenshotStart", str(self.screenshotStart.text()))
        update_settings("screenshotEnd", str(self.screenshotEnd.text()))
        if self.autoUploadScreenshot.isChecked():
            update_settings("autoUploadScreenshot", "True")
        else:
            update_settings("autoUploadScreenshot", "")
        if self.pasteScreenshotUrl.isChecked():
            update_settings("pasteScreenshotUrl", "True")
        else:
            update_settings("pasteScreenshotUrl", "")
        if self.deleteScreenshot.isChecked():
            update_settings("deleteScreenshot", "True")
        else:
            update_settings("deleteScreenshot", "")
        if self.makeDir.isChecked():
            update_settings("makeDir", "True")
        else:
            update_settings("makeDir", "")
        if self.renameFile.isChecked():
            update_settings("renameFile", "True")
        else:
            update_settings("renameFile", "")


class UploadPictureThread(QThread):
    # 创建一个信号，用于在数据处理完毕后与主线程通信
    result_signal = pyqtSignal(bool, dict, str, bool)

    def __init__(self, figureBedPath, figureBedToken, screenshot_path, is_cover):
        super().__init__()
        self.figureBedPath = figureBedPath
        self.figureBedToken = figureBedToken
        self.screenshot_path = screenshot_path
        self.is_cover = is_cover

    def run(self):
        try:
            # 这里放置耗时的HTTP请求操作
            upload_success, api_response = upload_screenshot(self.figureBedPath, self.figureBedToken,
                                                             self.screenshot_path)

            # 发送信号，包括请求的结果
            print("上传图床成功，开始返回结果")
            self.result_signal.emit(upload_success, api_response, self.screenshot_path, self.is_cover)
            print("返回结果成功")
            # self.result_signal(upload_success,api_response)
        except Exception as e:
            print(f"异常发生: {e}")
            self.result_signal.emit(False, f"异常发生: {e}", self.screenshot_path, self.is_cover)
            # 这里可以发射一个包含错误信息的信号


class UploadFreePictureThread(QThread):
    # 创建一个信号，用于在数据处理完毕后与主线程通信
    result_signal = pyqtSignal(bool, str, str, bool)

    def __init__(self, figureBedPath, figureBedToken, screenshot_path, is_cover):
        super().__init__()
        self.figureBedPath = figureBedPath
        self.figureBedToken = figureBedToken
        self.screenshot_path = screenshot_path
        self.is_cover = is_cover

    def run(self):
        try:
            # 这里放置耗时的HTTP请求操作
            upload_success, api_response = upload_free_screenshot(self.figureBedPath, self.figureBedToken,
                                                                  self.screenshot_path)

            # 发送信号，包括请求的结果
            print("上传图床成功，开始返回结果")
            self.result_signal.emit(upload_success, api_response, self.screenshot_path, self.is_cover)
            print("返回结果成功")
            # self.result_signal(upload_success,api_response)
        except Exception as e:
            print(f"异常发生: {e}")
            self.result_signal.emit(False, f"异常发生: {e}", self.screenshot_path, self.is_cover)
            # 这里可以发射一个包含错误信息的信号


class MakeTorrentThread(QThread):
    # 创建一个信号，用于在数据处理完毕后与主线程通信
    result_signal = pyqtSignal(bool, str)

    def __init__(self, folder_path, torrent_path):
        super().__init__()
        self.folder_path = folder_path
        self.torrent_path = torrent_path

    def run(self):
        try:
            # 这里放置耗时的制作torrent操作
            get_success, response = create_torrent(self.folder_path, self.torrent_path)

            # 发送信号
            print("Torrent请求成功，开始等待返回结果")
            self.result_signal.emit(get_success, response)
            print("返回结果成功")
            # self.result_signal(upload_success,api_response)
        except Exception as e:
            print(f"异常发生: {e}")
            # 这里可以发射一个包含错误信息的信号
