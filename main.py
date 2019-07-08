import wx
import json
import os
import subprocess
import signal
import sys
import datetime
#https://www.itread01.com/p/527729.html
#r = os.popen("echo abc")
#print(r.read())
class SmartMiner(wx.Frame):
    """
    A Frame that says Hello World
    """

    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(SmartMiner, self).__init__(*args, **kw)
        self.readDefaultParameter()
        self.version = "v1.0"
        self.versionClaymore = "v14.0"
        self.running = False
        self.helpAuthor = True
        self.PID = 0

        # create a panel in the frame
        pnl = wx.Panel(self)

        #bat txt
        self.cmdTxt = wx.StaticText(pnl, label="請輸入參數(按下Start後自動儲存)", pos=(10,10))
        self.command = wx.TextCtrl(pnl, id = -1,value=self.config['command'], pos=(10, 30),size=(600, 25))
        self.command.label = "command"
        font = self.cmdTxt.GetFont()
        font.PointSize += 2
        self.cmdTxt.SetFont(font)

        #pool pool
        self.poolTxt = wx.StaticText(pnl, label="礦池地址", pos=(10,80))
        self.pool = wx.TextCtrl(pnl, id = -1,value=self.config['pool'], pos=(80, 75),size=(310, 25))
        self.pool.label = "pool"
        font = self.poolTxt.GetFont()
        font.PointSize += 2
        self.poolTxt.SetFont(font)

        #pool wallet
        self.walletTxt = wx.StaticText(pnl, label="錢包地址", pos=(10,120))
        self.wallet = wx.TextCtrl(pnl, id = -1,value=self.config['ewal'] , pos=(80, 115),size=(310, 25))
        self.wallet.label = "wallet"
        font = self.walletTxt.GetFont()
        font.PointSize += 2
        self.walletTxt.SetFont(font)

        #pool eworker
        self.workerTxt = wx.StaticText(pnl, label="礦工名稱", pos=(10,160))
        self.worker = wx.TextCtrl(pnl, id = -1,value=self.config['eworker'], pos=(80, 155),size=(310, 25))
        self.worker.label = "worker"
        font = self.workerTxt.GetFont()
        font.PointSize += 2
        self.workerTxt.SetFont(font)

        #pool email
        self.emailTxt = wx.StaticText(pnl, label="Email", pos=(10,200))
        self.email = wx.TextCtrl(pnl, id = -1,value=self.config['email'], pos=(80, 195),size=(310, 25))
        self.email.label = "email"
        font = self.emailTxt.GetFont()
        font.PointSize += 2
        self.emailTxt.SetFont(font)

        #Time
        self.versionTxt = wx.StaticText(pnl, label=str(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')), pos=(400,72))
        font = self.versionTxt.GetFont()
        font.PointSize += 5
        self.versionTxt.SetFont(font)

        #tune tyoe
        self.timer1 = wx.RadioButton(pnl, label='契約用時間', pos=(400, 105))
        self.timer2 = wx.RadioButton(pnl, label='住商簡易型時間', pos=(400, 130))

        self.timer1.Bind(wx.EVT_RADIOBUTTON, self.onChecked)
        self.timer2.Bind(wx.EVT_RADIOBUTTON, self.onChecked)

        #help author checkBox
        self.helpAuthorCheckBox = wx.CheckBox(pnl, -1, "也幫作者挖10分鐘(感恩)", pos=[400,150] ,size = [300,30])
        self.helpAuthorCheckBox.Bind(wx.EVT_CHECKBOX, self.onCheckedHelpAuthor)

        #Start
        self.start = wx.Button(pnl, -1, "Start",pos=[520,185],size=(80, 40))
        font = self.start.GetFont()
        font.PointSize += 5
        self.start.SetFont(font)
        self.start.Bind(wx.EVT_BUTTON, self.startClicked)

        #Status
        self.st = wx.StaticText(pnl, label="暫停", pos=(400,185))
        font = self.st.GetFont()
        font.PointSize += 15
        font = font.Bold()
        self.st.SetFont(font)

        #version
        self.versionTxt = wx.StaticText(pnl, label="時間礦工"+self.version+" (Claymore "+self.versionClaymore+")", pos=(10,230))
        font = self.versionTxt.GetFont()
        font.PointSize += 5
        self.versionTxt.SetFont(font)

        self.Bind(wx.EVT_TEXT,self.OnTyped)
        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Bug回報或其他合作:lkm543@gmail.com")

    def writeModifiedParameter(self):
        with open('config.txt', 'w') as file:
            file.write(json.dumps(self.config))

    def readDefaultParameter(self):
        with open('config.txt') as f:
            self.config = json.load(f)

    def OnTyped(self,e):
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
        print (cb.GetLabel(), ' is clicked', cb.GetValue())

    def newVersion(self):
        return True

    def startClicked(self, event):
        """Close the frame, terminating the application."""
        self.writeModifiedParameter()
        self.running = not self.running
        if self.running:
            self.command.Disable()
            self.pool.Disable()
            self.worker.Disable()
            self.wallet.Disable()
            self.email.Disable()
            self.st.SetLabel("運行中")
            self.start.SetLabel("Stop")
            #subprocess.call("./Claymore/EthDcrMiner64.exe -epool eu1.ethermine.org:4444 -ewal 0xD69af2A796A737A103F12d2f0BCC563a13900E6F -epsw x")
            #with open('Claymore\start.bat', 'w') as file:
            #    file.writerow("Claymore/EthDcrMiner64.exe -epool "+self.config['pool']+" -ewal 0xD69af2A796A737A103F12d2f0BCC563a13900E6F -epsw x")
            commandLine = str("Claymore\start.bat")
            p = subprocess.Popen(commandLine, shell=False)
            self.PID = p.pid
        else:
            self.command.Enable()
            self.pool.Enable()
            self.worker.Enable()
            self.wallet.Enable()
            self.email.Enable()
            self.st.SetLabel("暫停")
            self.start.SetLabel("Start")
            os.kill(self.PID, signal.CTRL_C_EVENT)
        #self.status.SetLabel(self.state)
        #print("H")
        #self.Close(True)
    def onCheckedHelpAuthor(self, e):
        self.helpAuthor = not self.helpAuthor
        print("helpAuthor:",self.helpAuthor)
if __name__ == '__main__':

    app = wx.App()
    frm = SmartMiner(None, title='時間挖礦v1.0')
    frm.SetMaxSize(wx.Size(640,400))
    frm.SetMinSize(wx.Size(640,400))
    frm.Show()
    app.MainLoop()
