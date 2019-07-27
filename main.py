import datetime
import json
import os
import signal
import subprocess

import wx
# pyinstaller -F -w .\main.py
# pyinstaller -F .\main.py --noconsole

# TODO: Check time type
class SmartMiner(wx. Frame):

    def __init__(self, *args, **kw):
        #  ensure the parent's __init__ is called
        super(SmartMiner, self).__init__(*args, **kw)
        self.readDefaultParameter()
        self.version = "v1.0"
        self.versionClaymore = "v14.0"
        self.running = False
        self.helpAuthor = True
        self.p = None
        self.PID = None

        #  create a panel in the frame
        self.pnl = wx.Panel(self)

        # bat txt
        cmdLabel = "請輸入參數(按下Start後自動儲存)"
        self.cmdTxt = wx.StaticText(self.pnl, label=cmdLabel, pos=(10, 10))
        self.command = wx.TextCtrl(self.pnl,
                                   id=-1,
                                   value=self.config['command'],
                                   pos=(10, 30),
                                   size=(600, 25))
        self.command.label = "command"
        font = self.cmdTxt.GetFont()
        font.PointSize += 2
        self.cmdTxt.SetFont(font)

        # pool
        self.poolTxt = wx.StaticText(self.pnl,
                                     label="礦池地址",
                                     pos=(10, 80))
        self.pool = wx.TextCtrl(self.pnl,
                                id=-1,
                                value=self.config['pool'],
                                pos=(80, 75),
                                size=(310, 25))
        self.pool.label = "pool"
        font = self.poolTxt.GetFont()
        font.PointSize += 2
        self.poolTxt.SetFont(font)

        # pool wallet
        self.walletTxt = wx.StaticText(self.pnl,
                                       label="錢包地址",
                                       pos=(10, 120))
        self.wallet = wx.TextCtrl(self.pnl,
                                  id=-1,
                                  value=self.config['ewal'],
                                  pos=(80, 115),
                                  size=(310, 25))
        self.wallet.label = "wallet"
        font = self.walletTxt.GetFont()
        font.PointSize += 2
        self.walletTxt.SetFont(font)

        # pool eworker
        self.workerTxt = wx.StaticText(self.pnl,
                                       label="礦工名稱",
                                       pos=(10, 160))
        self.worker = wx.TextCtrl(self.pnl,
                                  id=-1,
                                  value=self.config['eworker'],
                                  pos=(80, 155),
                                  size=(310, 25))
        self.worker.label = "worker"
        font = self.workerTxt.GetFont()
        font.PointSize += 2
        self.workerTxt.SetFont(font)

        # pool email
        self.emailTxt = wx.StaticText(self.pnl,
                                      label="Email",
                                      pos=(10, 200))
        self.email = wx.TextCtrl(self.pnl,
                                 id=-1,
                                 value=self.config['email'],
                                 pos=(80, 195),
                                 size=(310, 25))
        self.email.label = "email"
        font = self.emailTxt.GetFont()
        font.PointSize += 1
        self.emailTxt.SetFont(font)

        # Scrolling status text
        self.minerStatus = wx.TextCtrl(self.pnl,
                                       value='------等待開始中------\n',
                                       style=wx.TE_MULTILINE | wx.TE_READONLY,
                                       pos=(10, 270),
                                       size=(1240, 500))
        self.minerStatus.SetBackgroundColour((0, 0, 0))
        self.minerStatus.SetForegroundColour((200, 200, 200))
        font = self.minerStatus.GetFont()
        font.PointSize += 2
        self.minerStatus.SetFont(font)

        # Timer
        time = str(datetime.datetime.now().strftime('%Y/%m/%d\n\n%H:%M:%S'))
        self.timeTxt = wx.StaticText(self.pnl, label=time, pos=(400, 72))
        font = self.timeTxt.GetFont()
        font.PointSize += 5
        self.timeTxt.SetFont(font)

        # Time
        self.onTimer(None)
        self.timer = wx.Timer(self, -1)
        self.timer.Start(1000)
        self.Bind(wx.EVT_TIMER, self.onTimer)

        # tune tyoe
        self.timer1 = wx.RadioButton(self.pnl,
                                     label='契約用時間',
                                     pos=(400, 105),
                                     style=wx.RB_GROUP)
        self.timer2 = wx.RadioButton(self.pnl,
                                     label='住商簡易型時間',
                                     pos=(400, 130))

        self.timer1.Bind(wx.EVT_RADIOBUTTON, self.onChecked)
        self.timer2.Bind(wx.EVT_RADIOBUTTON, self.onChecked)

        # help author checkBox
        self.helpAuthorCheckBox = wx.CheckBox(self.pnl,
                                              id=-1,
                                              label="也幫作者挖10分鐘(感恩)",
                                              pos=[400, 150],
                                              size=[300, 30])
        self.helpAuthorCheckBox.Bind(wx.EVT_CHECKBOX, self.onCheckedHelpAuthor)
        self.helpAuthorCheckBox.SetValue(True)

        # Start
        self.start = wx.Button(self.pnl,
                               -1,
                               "Start",
                               pos=[520, 185],
                               size=(80, 40))
        font = self.start.GetFont()
        font.PointSize += 5
        self.start.SetFont(font)
        self.start.Bind(wx.EVT_BUTTON, self.startClicked)

        # Status
        self.st = wx.StaticText(self.pnl, label="暫停", pos=(400, 185))
        font = self.st.GetFont()
        font.PointSize += 15
        font = font.Bold()
        self.st.SetFont(font)

        # version
        versionTxt = f"時間礦工{self.version} (Claymore{self.versionClaymore})"
        self.versionTxt = wx.StaticText(self.pnl,
                                        label=versionTxt,
                                        pos=(10, 230))
        font = self.versionTxt.GetFont()
        font.PointSize += 5
        self.versionTxt.SetFont(font)

        self.Bind(wx.EVT_TEXT, self.OnTyped)
        #  and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Bug回報或合作:lkm543@gmail.com")

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
            elif label == 'email':
                self.config['email'] = txt
            elif label == 'wallet':
                self.config['ewal'] = txt
            print(self.config)

    def onChecked(self, e):
        cb = e.GetEventObject()
        print(cb.GetLabel(), 'is clicked', cb.GetValue())

    def newVersion(self):
        return True

    def startClicked(self, event):
        # TODO: Check 離峰與否
        self.writeModifiedParameter()
        if not self.running:
            commandLine = "start.bat"
            try:
                self.minerStatus.AppendText('------開始運行Claymore.....(請稍待5秒)------\n')
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
                if self.p is not None:
                    self.running = not self.running
                    self.command.Disable()
                    self.pool.Disable()
                    self.worker.Disable()
                    self.wallet.Disable()
                    self.email.Disable()
                    self.st.SetLabel("運行中")
                    self.start.SetLabel("Stop")
            except Exception as e:
                print(e)
        else:
            self.stopMiner()

    def stopMiner(self):
        self.command.Enable()
        self.pool.Enable()
        self.worker.Enable()
        self.wallet.Enable()
        self.email.Enable()
        self.st.SetLabel("暫停")
        self.start.SetLabel("Start")
        os.kill(self.PID, signal.CTRL_C_EVENT)
        self.running = not self.running

    def onCheckedHelpAuthor(self, e):
        self.helpAuthor = not self.helpAuthor
        print("helpAuthor:", self.helpAuthor)

    def onTimer(self, event):
        # Timer
        time = str(datetime.datetime.now().strftime('%Y/%m/%d  %H:%M:%S'))
        self.timeTxt.SetLabel(time)
        # Check if the miner is alive or not
        if self.p is not None and self.running:
            poll = self.p.poll()
            if poll is not None:
                # p.subprocess is NOT alive
                lines = self.p.stdout.readlines()
                for line in lines:
                    miner_status = line.decode('utf-8', 'ignore')
                    print(miner_status)
                    self.minerStatus.AppendText(miner_status)
                self.stopMiner()
                self.minerStatus.AppendText('------Claymore已終止------\n')
                print('Miner stops......')
            # Read output of terminal
            else:
                try:
                    # Check the time
                    weekday = datetime.datetime.today().weekday() + 1
                    # print(f'Weekday:{weekday}')
                    lines = self.p.stdout.readlines()
                    for line in lines:
                        miner_status = line.decode('utf-8', 'ignore')
                        print(miner_status)
                        self.minerStatus.AppendText(miner_status)
                except Exception as e:
                    self.minerStatus.AppendText(f'{e}\n')


if __name__ == '__main__':

    app = wx.App()
    frm = SmartMiner(None, title='時間挖礦v1.0')
    frm.SetMaxSize(wx.Size(1280, 840))
    frm.SetMinSize(wx.Size(1280, 840))
    frm.Show()
    app.MainLoop()
