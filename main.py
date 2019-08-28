import datetime
import json
import os
import re
import signal
import subprocess
import webbrowser

import requests
import wx


# pyinstaller -F -w .\main.py
# TODO:載入雲端config
class SmartMiner(wx.Frame):
    def __init__(self, *args, **kw):
        #  ensure the parent's __init__ is called
        super(SmartMiner, self).__init__(*args, **kw)
        # Version of this release
        self.version = "1.0"
        self.Claymore = "14.7"
        # Latest release
        self.releaseNote, self.nationalHoliday = self.getVersion()
        self.latestVersion = self.releaseNote['version']
        self.latestClaymore = self.releaseNote['claymore']
        self.latestVersionURL = self.releaseNote['smartminer_url']
        self.latestClaymoreURL = self.releaseNote['claymore_url']
        self.readDefaultParameter()
        self.running = False
        # 0: bat 1:command 2:parm
        self.miner_mode = 0
        self.p = None
        self.PID = None
        self.stop_period = {
            1: {
                'start': 27000,
                'finish': 81000
            },
            2: {
                'start': 27000,
                'finish': 81000
            },
            3: {
                'start': 27000,
                'finish': 81000
            },
            4: {
                'start': 27000,
                'finish': 81000
            },
            5: {
                'start': 27000,
                'finish': 81000
            },
            6: {
                'start': 0,
                'finish': 0
            },
            7: {
                'start': 0,
                'finish': 0
            },
        }

        #  create a panel in the frame
        self.pnl = wx.Panel(self)

        # command
        self.command = wx.TextCtrl(self.pnl,
                                   id=-1,
                                   value=self.config['command'],
                                   pos=(40, 100),
                                   size=(600, 25))
        self.command.label = "command"

        # pool
        self.poolTxt = wx.StaticText(self.pnl, label="礦池地址", pos=(40, 165))
        self.pool = wx.TextCtrl(self.pnl,
                                id=-1,
                                value=self.config['pool'],
                                pos=(110, 160),
                                size=(310, 25))
        self.pool.label = "pool"
        font = self.poolTxt.GetFont()
        font.PointSize += 2
        self.poolTxt.SetFont(font)

        # pool wallet
        self.walletTxt = wx.StaticText(self.pnl, label="錢包地址", pos=(40, 205))
        self.wallet = wx.TextCtrl(self.pnl,
                                  id=-1,
                                  value=self.config['ewal'],
                                  pos=(110, 200),
                                  size=(310, 25))
        self.wallet.label = "wallet"
        font = self.walletTxt.GetFont()
        font.PointSize += 2
        self.walletTxt.SetFont(font)

        # pool eworker
        self.workerTxt = wx.StaticText(self.pnl, label="礦工名稱", pos=(40, 245))
        self.worker = wx.TextCtrl(self.pnl,
                                  id=-1,
                                  value=self.config['eworker'],
                                  pos=(110, 240),
                                  size=(310, 25))
        self.worker.label = "worker"
        font = self.workerTxt.GetFont()
        font.PointSize += 2
        self.workerTxt.SetFont(font)

        # Scrolling status text
        if self.checkPeak():
            miner_state = '------等待開始中(尖峰)------\n'
        else:
            miner_state = '------等待開始中(離峰)------\n'
        self.minerStatus = wx.TextCtrl(self.pnl,
                                       value=miner_state,
                                       style=wx.TE_MULTILINE | wx.TE_READONLY,
                                       pos=(10, 280),
                                       size=(630, 440))
        self.minerStatus.SetBackgroundColour((0, 0, 0))
        self.minerStatus.SetForegroundColour((200, 200, 200))
        font = self.minerStatus.GetFont()
        font.PointSize += 2
        self.minerStatus.SetFont(font)

        # Time
        time = str(datetime.datetime.now().strftime('%Y/%m/%d\n%H:%M:%S'))
        self.timeTxt = wx.StaticText(self.pnl, label=time, pos=(500, 10))
        font = self.timeTxt.GetFont()
        font.PointSize += 10
        self.timeTxt.SetFont(font)

        # Timer
        self.onTimer(None)
        self.timer = wx.Timer(self, -1)
        self.timer.Start(1000)
        self.Bind(wx.EVT_TIMER, self.onTimer)

        # tune tyoe
        self.mineMode1 = wx.RadioButton(self.pnl,
                                        label='使用自己的start.bat挖',
                                        name='miner_bat',
                                        pos=(10, 50))
        self.mineMode1.SetValue(True)
        self.command.Disable()
        self.pool.Disable()
        self.worker.Disable()
        self.wallet.Disable()
        self.mineMode2 = wx.RadioButton(self.pnl,
                                        label='輸入命令列挖',
                                        name='miner_command',
                                        pos=(10, 80))
        self.mineMode3 = wx.RadioButton(self.pnl,
                                        label='輸入參數',
                                        name='miner_parm',
                                        pos=(10, 140))
        font = self.mineMode1.GetFont()
        font.PointSize += 2
        self.mineMode1.SetFont(font)
        font = self.mineMode2.GetFont()
        font.PointSize += 2
        self.mineMode2.SetFont(font)
        font = self.mineMode3.GetFont()
        font.PointSize += 2
        self.mineMode3.SetFont(font)
        self.mineMode1.Bind(wx.EVT_RADIOBUTTON, self.onChecked)
        self.mineMode2.Bind(wx.EVT_RADIOBUTTON, self.onChecked)
        self.mineMode3.Bind(wx.EVT_RADIOBUTTON, self.onChecked)

        # Start
        self.start = wx.Button(self.pnl,
                               -1,
                               "Start",
                               pos=[430, 225],
                               size=(200, 40))
        font = self.start.GetFont()
        font.PointSize += 5
        self.start.SetFont(font)
        self.start.Bind(wx.EVT_BUTTON, self.startClicked)

        # Status
        if self.checkPeak():
            system_state = '暫停\n(尖峰)'
        else:
            system_state = '暫停\n(離峰)\n'
        self.st = wx.StaticText(self.pnl, label=system_state, pos=(430, 140))
        font = self.st.GetFont()
        font.PointSize += 12
        font = font.Bold()
        self.st.SetFont(font)

        # version
        versionTxt = f"時間礦工{self.version} (Claymore{self.Claymore})"
        self.versionTxt = wx.StaticText(self.pnl,
                                        label=versionTxt,
                                        pos=(10, 10))
        font = self.versionTxt.GetFont()
        font.PointSize += 5
        self.versionTxt.SetFont(font)

        self.Bind(wx.EVT_TEXT, self.OnTyped)
        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Bug回報或合作:lkm543@gmail.com")

        # New version recommendation
        if float(self.version) < float(self.latestVersion):
            self.onNewVersion()
        elif float(self.Claymore) < float(self.latestClaymore):
            self.onNewClaymoreVersion()

    def onNewClaymoreVersion(self):
        dlg = wx.MessageDialog(None, "新的Claymore釋出了，是否要下載?", "有新的版本喔",
                               wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            webbrowser.open(self.latestClaymoreURL, new=0, autoraise=True)
            dlg.Destroy()
            self.Close(True)

    def onNewVersion(self):
        dlg = wx.MessageDialog(None, "新的版本釋出了，是否要下載?", "有新的版本喔",
                               wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            webbrowser.open(self.latestVersionURL, new=0, autoraise=True)
            dlg.Destroy()
            self.Close(True)

    def writeModifiedParameter(self):
        with open('config.txt', 'w') as file:
            file.write(json.dumps(self.config))

    def readDefaultParameter(self):
        with open('config.txt') as f:
            self.config = json.load(f)

    def OnTyped(self, e):
        if self.minerStatus != e.GetEventObject():
            label = e.GetEventObject().label
            txt = e.GetString()
            if label == 'command':
                self.config['command'] = txt
            elif label == 'pool':
                self.config['pool'] = txt
            elif label == 'worker':
                self.config['eworker'] = txt
            elif label == 'wallet':
                self.config['ewal'] = txt
            print(self.config)

    def checkPeak(self):
        return False
        now_timestamp = datetime.datetime.now().timestamp()
        weekday = datetime.datetime.today().weekday() + 1
        now = datetime.datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds = (now - midnight).seconds
        start = self.stop_period[weekday]['start']
        finish = self.stop_period[weekday]['finish']
        for nH in self.nationalHoliday:
            if nH['start'] < now_timestamp < nH['finish']:
                return False
        if start < seconds < finish:
            return True
        else:
            return False

    def onChecked(self, e):
        cb = e.GetEventObject()
        checked_label = cb.GetName()
        if checked_label == 'miner_bat':
            self.miner_mode = 0
            self.command.Disable()
            self.pool.Disable()
            self.worker.Disable()
            self.wallet.Disable()
        elif checked_label == 'miner_command':
            self.miner_mode = 1
            self.command.Enable()
            self.pool.Disable()
            self.worker.Disable()
            self.wallet.Disable()
        elif checked_label == 'miner_parm':
            self.miner_mode = 2
            self.pool.Enable()
            self.worker.Enable()
            self.wallet.Enable()
            self.command.Disable()
        print(cb.GetName(), 'is clicked', cb.GetValue())

    def startClicked(self, event):
        self.writeModifiedParameter()
        if not self.running:
            if self.miner_mode == 1:
                string = "setx GPU_FORCE_64BIT_PTR 0\n"
                string += "setx GPU_MAX_HEAP_SIZE 100\n"
                string += "setx GPU_USE_SYNC_OBJECTS 1\n"
                string += "setx GPU_MAX_ALLOC_PERCENT 100\n"
                string += "setx GPU_SINGLE_ALLOC_PERCENT 100\n"
                string += self.config['command']
                with open('Claymore/start.bat', 'w') as file:
                    print("Write command to start.bat")
                    file.write(string)
            elif self.miner_mode == 2:
                string = "setx GPU_FORCE_64BIT_PTR 0\n"
                string += "setx GPU_MAX_HEAP_SIZE 100\n"
                string += "setx GPU_USE_SYNC_OBJECTS 1\n"
                string += "setx GPU_MAX_ALLOC_PERCENT 100\n"
                string += "setx GPU_SINGLE_ALLOC_PERCENT 100\n"
                string += f"EthDcrMiner64.exe -epool {self.config['pool']} " \
                          f"-ewal {self.config['ewal']} " \
                          f"-eworker {self.config['eworker']} "
                with open('Claymore/start.bat', 'w') as file:
                    print("Write parms to start.bat")
                    file.write(string)

            commandLine = "start.bat"
            try:
                peak = self.checkPeak()
                # 離峰
                if not peak:
                    self.minerStatus.AppendText(
                        '------開始運行Claymore------\n')
                    cwd = os.path.dirname(os.path.realpath(__file__))
                    cwd += "\\Claymore\\"
                    self.p = subprocess.Popen(commandLine,
                                              cwd=cwd,
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE,
                                              stdin=subprocess.PIPE,
                                              shell=True,
                                              bufsize=-1)
                    self.PID = self.p.pid
                    # 如果開啟PID成功
                    if self.p is not None:
                        self.running = not self.running
                        self.command.Disable()
                        self.pool.Disable()
                        self.worker.Disable()
                        self.wallet.Disable()
                        self.st.SetLabel("運行中\n(離峰)")
                        self.start.SetLabel("Stop")
                # 尖峰
                else:
                    self.running = not self.running
                    self.command.Disable()
                    self.pool.Disable()
                    self.worker.Disable()
                    self.wallet.Disable()
                    self.st.SetLabel("運行中\n(尖峰等待中)")
                    self.start.SetLabel("Stop")
            except Exception as e:
                print(e)
        else:
            # 運行中，終止程序
            self.stopMiner()

    def stopMiner(self):
        self.command.Enable()
        self.pool.Enable()
        self.worker.Enable()
        self.wallet.Enable()
        self.st.SetLabel("暫停")
        self.start.SetLabel("Start")
        try:
            os.kill(self.PID, signal.CTRL_C_EVENT)
        except Exception:
            print(Exception)
        self.running = not self.running

    def getVersion(self):
        url = 'https://www.lkm543.site/smartMiner.json'
        try:
            # TODO: Key not exist check
            data = requests.get(url).json()
            print(f"Author : {data['author']}")
            print(f"Contact: {data['contact']}")
            print(f"Website: {data['website']}")
            releaseNote = data['versionNote']
            nationalHoliday = data['nationalHoliday']
            if 'version' not in releaseNote[0].keys():
                releaseNote[0]['version'] = 0.0
            if 'claymore' not in releaseNote[0].keys():
                releaseNote[0]['claymore'] = 0.0
            if 'smartminer_url' not in releaseNote[0].keys():
                releaseNote[0]['smartminer_url'] = \
                    "https://www.lkm543.site/smartMiner.rar"
            if 'claymore_url' not in releaseNote[0].keys():
                releaseNote[0]['claymore_url'] = \
                    "https://www.lkm543.site/Claymore.rar"
            if 'upload_note' not in releaseNote[0].keys():
                releaseNote[0]['upload_note'] = "抓取失敗"
            return releaseNote[0], nationalHoliday
        except Exception:
            data = {
                "version": "0.0",
                "claymore": "0.0",
                "smartminer_url": "https://www.lkm543.site/smartMiner.rar",
                "claymore_url": "https://www.lkm543.site/Claymore.rar",
                "upload_note": "抓取失敗"
            }
            nationalHoliday = [{"start": 0, "finish": 0}]
            return data, nationalHoliday

    def onTimer(self, event):
        # Timer
        time = str(datetime.datetime.now().strftime('%Y/%m/%d\n%H:%M:%S'))
        self.timeTxt.SetLabel(time)
        # Check if the miner is alive or not
        if self.p is not None and self.running:
            print("It should running")
            # The poll() method will return
            # the exit code if the process is completed.
            # None if the process is still running.
            poll = self.p.poll()
            if poll is not None:
                print("But it is not running")
                # p.subprocess is NOT alive
                self.read_miner()
                self.stopMiner()
                self.minerStatus.AppendText('------Claymore已終止------\n')
                print('Miner stops......')
            # Read output of terminal
            else:
                print("And it is actually running")
                try:
                    self.read_miner()
                    # Check the time
                    if self.checkPeak():
                        self.stopMiner()
                except Exception as e:
                    self.minerStatus.AppendText(f'{e}\n')

    def read_miner(self):
        lines = self.p.stdout.readlines()
        for line in lines:
            miner_status = line.decode('cp950').encode('utf-8', 'ignore')
            miner_status = miner_status.rstrip()
            miner_status += '\n'.encode('utf-8', 'ignore')
            print(miner_status.decode('utf-8'))
            self.minerStatus.AppendText(miner_status)

    def parse_claymore(self, text):
        pass

if __name__ == '__main__':

    app = wx.App()
    frm = SmartMiner(None, title='時間挖礦v1.0')
    frm.SetMaxSize(wx.Size(670, 840))
    frm.SetMinSize(wx.Size(670, 840))
    frm.Show()
    app.MainLoop()
