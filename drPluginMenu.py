#   Programmer: Daniel Pozmanter
#   E-mail:     drpython@bluebottle.com
#   Note:       You must reply to the verification e-mail to get through.
#
#   Copyright 2003-2010 Daniel Pozmanter
#
#   Distributed under the terms of the GPL (GNU Public License)
#
#    DrPython is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#Plugins Menu

import os, shutil, sys
import wx
import drScrolledMessageDialog
import drFileDialog
from drMenu import drMenu

class drPluginConfigureMenu(drMenu):
    def __init__(self, parent):
        drMenu.__init__(self, parent)

        self.parent = parent

        self.ID_INSTALL = 4300
        self.ID_INSTALL_PY = 4301
        self.ID_UNINSTALL = 4302
        self.ID_INDEX = 4303

        self.wildcard = "DrPython Plugin (*.py)|*.py"

        #self.Append(self.ID_INSTALL, "&Install...") #install from sourceforge is not working anymore
        #todo: rework if possible
        self.Append(self.ID_INSTALL_PY, "Install From Py...")
        self.Append(self.ID_UNINSTALL, "&UnInstall...")
        self.Append(self.ID_INDEX, "&Edit Indexes...")

        self.parent.Bind(wx.EVT_MENU, self.OnInstall, id=self.ID_INSTALL)
        self.parent.Bind(wx.EVT_MENU, self.OnInstallFromPy, id=self.ID_INSTALL_PY)
        self.parent.Bind(wx.EVT_MENU, self.OnUnInstall, id=self.ID_UNINSTALL)
        self.parent.Bind(wx.EVT_MENU, self.OnEditIndex, id=self.ID_INDEX)

    def OnEditIndex(self, event):
        from drPluginDialog import drEditIndexDialog
        d = drEditIndexDialog(self.parent)
        d.ShowModal()
        d.Destroy()

    def OnInstall(self, event):
        from drPluginDialog import drPluginInstallWizard
        img = wx.Image(os.path.join(self.parent.bitmapdirectory, "install.wizard.png"), wx.BITMAP_TYPE_PNG)
        installWizard = drPluginInstallWizard(self.parent, "Install DrPython Plugin(s)", wx.BitmapFromImage(img))
        installWizard.Run()

    def OnInstallFromPy(self, event):
        dlg = drFileDialog.FileDialog(self.parent, "Select Plugin to Install", self.wildcard)
        if self.parent.pluginsdirectory:
            try:
                dlg.SetDirectory(self.parent.pluginsdirectory)
            except:
                drScrolledMessageDialog.ShowMessage(self.parent, ("Error Setting Default Directory To: "
                                                    + self.parent.pluginsdirectory), "DrPython Error")
        if dlg.ShowModal() == wx.ID_OK:
            if not os.path.exists(self.parent.pluginsdirectory):
                os.mkdir(self.parent.pluginsdirectory)
            pluginfile = dlg.GetPath().replace('\\', '/')
            pluginrfile = os.path.join(self.parent.pluginsdirectory, os.path.split(pluginfile)[1])
            pluginpath, plugin = os.path.split(pluginfile)
            i = plugin.find(".py")
            if i == -1:
                drScrolledMessageDialog.ShowMessage(self.parent, ("Plugins must be .py files."), "DrPython Error")
            plugininstallfile = pluginfile + ".install"
            continueinstallation = True
            if os.path.exists(plugininstallfile):
                f = open(plugininstallfile, 'r')
                scripttext = f.read()
                f.close()

                try:
                    code = compile((scripttext + '\n'), plugininstallfile, "exec")
                except:
                    drScrolledMessageDialog.ShowMessage(self.parent, ("Error compiling install script."), "Error", wx.DefaultPosition, (550,300))
                    return

                try:
                    cwd = os.getcwd()
                    os.chdir(pluginpath)
                    exec(code)
                    continueinstallation = Install(self.parent)
                    os.chdir(cwd)
                except:
                    drScrolledMessageDialog.ShowMessage(self.parent, ("Error running install script."), "Error", wx.DefaultPosition, (550,300))
                    return
            if not continueinstallation:
                return
            plugin = plugin[:i]
            pluginsfile = os.path.join(self.parent.preferencesdirectory, "default.idx")
            if not os.path.exists(pluginsfile):
                f = open(pluginsfile, 'wb')
                f.write('\n')
                f.close()
            try:
                copyf = True
                if os.path.exists(pluginrfile):
                    answer = wx.MessageBox("Overwrite'" + pluginrfile + "'?", "DrPython", wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
                    if answer == wx.NO:
                        copyf = False
                if copyf:
                    shutil.copyfile(pluginfile, pluginrfile)
                    #there could be an error check: if idx file does not exist in source, simply create one.
                    shutil.copyfile(os.path.splitext(pluginfile)[0] + ".idx",
                                    os.path.splitext(pluginrfile)[0] + ".idx")
                try:
                    f = open(pluginsfile, 'rU')
                    pluginstoload = [x.strip() for x in f]
                    f.close()
                except:
                    pluginstoload = []
                try:
                    pluginstoload.index(plugin)
                except:
                    f = open(pluginsfile, 'w')
                    for p in pluginstoload:
                        f.write(p + "\n")
                    f.write(plugin)
                    f.close()

            except:
                drScrolledMessageDialog.ShowMessage(self.parent, ("Error with: " + pluginfile), "Install Error")
                return

    def OnUnInstall(self, event):
        from drPluginDialog import drPluginUnInstallWizard
        img = wx.Image(os.path.join(self.parent.bitmapdirectory, "uninstall.wizard.png"), wx.BITMAP_TYPE_PNG)
        uninstallWizard = drPluginUnInstallWizard(self.parent, "UnInstall DrPython Plugin(s)", wx.BitmapFromImage(img))
        uninstallWizard.Run()

class drPluginIndexMenu(wx.Menu):
    def __init__(self, parent):
        wx.Menu.__init__(self)

        self.ID_LOAD_PLUGIN_BASE = 4505

        self.parent = parent

        self.indexes = []
        self.loadedindexes = [os.path.join(self.parent.preferencesdirectory, "default.idx")]

        self.setupMenu()

    def OnLoadPluginsFromIndex(self, event):
        idnum = event.GetId()
        i = idnum - self.ID_LOAD_PLUGIN_BASE
        index = self.indexes[i]
        try:
            f = open(index, 'r')
            pluginstoload = f.read().rstrip().split('\n')
            f.close()
            for plugin in pluginstoload:
                try:
                    self.parent.InitializePlugin(plugin)
                except:
                    errstring = str(sys.exc_info()[0]).lstrip("exceptions.") + ": " + str(sys.exc_info()[1])

                    drScrolledMessageDialog.ShowMessage(self.parent, ("Error loading plugin: " + plugin + "\n\n" + errstring), "Load Error")
            self.loadedindexes.append(self.indexes[i])
            self.reloadMenu()
        except:
            drScrolledMessageDialog.ShowMessage(self.parent, ("Error loading plugins from: " + index), "Load Error")

    def setupMenu(self):
        files = os.listdir(self.parent.pluginsdirectory)
        self.indexes = []

        #Added By Franz
        pluginsfile = os.path.join(self.parent.preferencesdirectory, "default.idx")
        if not os.path.exists(pluginsfile):
            return
        pluginstoload = []
        try:
            f = open(pluginsfile, 'rU')
            pluginstoload = [x.strip() for x in f]
            f.close()
        except:
            #Return added by Dan
            return
        #/Franz

        x = 0
        loadpluginsfromindexfiles = []
        for f in files:
            if f.find(".idx") > -1 and f != "default.idx":
                index = os.path.join (self.parent.pluginsdirectory, f)
                if not (index in self.loadedindexes):
                    if not os.path.splitext(os.path.basename(index))[0] in pluginstoload:
                        self.indexes.append(index)
                        loadpluginsfromindexfiles.append(os.path.basename(f))
                        #self.Append(self.ID_LOAD_PLUGIN_BASE + x, str(os.path.basename(f)))
                        #self.parent.Bind(wx.EVT_MENU, self.OnLoadPluginsFromIndex, id=self.ID_LOAD_PLUGIN_BASE+x)
                        x = x + 1


        #sort alphabetically (after self.indexes after loadpluginsfromindexfiles)
        #only if they are not empty
        if self.indexes and loadpluginsfromindexfiles:
            loadpluginsfromindexfiles, self.indexes = zip(*sorted(zip(loadpluginsfromindexfiles,self.indexes)))

        loadpluginsfromindexfiles = list(loadpluginsfromindexfiles)
        self.indexes = list(self.indexes)

        x = 0
        for f in loadpluginsfromindexfiles:
            self.indexes.append(index)
            self.Append(self.ID_LOAD_PLUGIN_BASE + x, str(f))
            self.parent.Bind(wx.EVT_MENU, self.OnLoadPluginsFromIndex, id=self.ID_LOAD_PLUGIN_BASE+x)
            x = x + 1

    def reloadMenu(self):
        mnuitems = self.GetMenuItems()
        num = len(mnuitems)
        x = 0
        while x < num:
            self.Remove(self.ID_LOAD_PLUGIN_BASE + x)
            x = x + 1
        self.setupMenu()

class drPluginFunctionMenu(wx.Menu):
    def __init__(self, parent, function_id_base, functionstring, function):
        wx.Menu.__init__(self)

        self.ID_BASE = function_id_base

        self.functionstring = functionstring

        self.function = function

        self.parent = parent

        self.pluginsArray = []
        self.pluginsMenuArray = []

    def GetInsertPosition(self, plugin):
        x = 0
        l = len(self.pluginsMenuArray)
        while x < l:
            if plugin > self.pluginsMenuArray[x]:
                x += 1
            else:
                return x
        return x

    def AddItem(self, plugin):
        try:
            i = self.parent.LoadedPlugins.index(plugin)
            exec(compile("self.parent.PluginModules[i]" + self.functionstring, plugin, "exec"))
            x = len(self.pluginsArray)
            i = self.GetInsertPosition(plugin)
            self.pluginsMenuArray.insert(i, plugin)
            self.pluginsArray.append(plugin)
            self.Insert(i, self.ID_BASE + x, plugin)
            self.parent.Bind(wx.EVT_MENU, self.function, id=self.ID_BASE + x)
        except:
            pass

class drPluginAboutMenu(drPluginFunctionMenu):
    def __init__(self, parent):
        self.ID_LOAD_PLUGIN_ABOUT_BASE = 4305

        drPluginFunctionMenu.__init__(self, parent, self.ID_LOAD_PLUGIN_ABOUT_BASE, ".OnAbout", self.OnLoadPluginsAbout)

    def OnLoadPluginsAbout(self, event):
        idnum = event.GetId()
        i = idnum - self.ID_LOAD_PLUGIN_ABOUT_BASE
        plugin = self.pluginsArray[i]
        try:
            i = self.parent.LoadedPlugins.index(plugin)
            self.parent.PluginModules[i].OnAbout(self.parent)
        except:
            drScrolledMessageDialog.ShowMessage(self.parent, "Error With About.", "Plugin About Error")

class drPluginHelpMenu(drPluginFunctionMenu):
    def __init__(self, parent):
        self.ID_LOAD_PLUGIN_HELP_BASE = 4705

        drPluginFunctionMenu.__init__(self, parent, self.ID_LOAD_PLUGIN_HELP_BASE, ".OnHelp", self.OnLoadPluginsHelp)

    def OnLoadPluginsHelp(self, event):
        idnum = event.GetId()
        i = idnum - self.ID_LOAD_PLUGIN_HELP_BASE
        plugin = self.pluginsArray[i]
        try:
            i = self.parent.LoadedPlugins.index(plugin)
            self.parent.PluginModules[i].OnHelp(self.parent)
        except:
            drScrolledMessageDialog.ShowMessage(self.parent, ("Error With Help."), "Plugin Help Error")

class drPluginPreferencesMenu(drPluginFunctionMenu):
    def __init__(self, parent):
        self.ID_LOAD_PLUGIN_PREFS_BASE = 4905

        drPluginFunctionMenu.__init__(self, parent, self.ID_LOAD_PLUGIN_PREFS_BASE, ".OnPreferences", self.OnLoadPluginsPreferences)

    def OnLoadPluginsPreferences(self, event):
        idnum = event.GetId()
        i = idnum - self.ID_LOAD_PLUGIN_PREFS_BASE
        plugin = self.pluginsArray[i]
        try:
            i = self.parent.LoadedPlugins.index(plugin)
            self.parent.PluginModules[i].OnPreferences(self.parent)
        except:
            drScrolledMessageDialog.ShowMessage(self.parent, ("Error With Help."), "Plugin Help Error")
