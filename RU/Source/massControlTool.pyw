import os
import paramiko
import socket
import time
from tkinter import *
from tkinter.filedialog import askopenfilenames
from datetime import datetime
from ast import literal_eval

class massControlTool:
    def __init__(self):
        self.players = []
        self.selected_players = []
        self.array_files = []
        self.array_commands = []
        self.isRouters = False
        self.routerWaitForAnswerTime = 3

        # DEFAULTS
        self.DEFAULT_sshport = 22
        self.DEFAULT_listParams = [0,"players.txt"]

        self.sshport = self.DEFAULT_sshport
        self.listParams = self.DEFAULT_listParams

        self.settingsFileName = "settings.cfg"
        self.infoText1 = "Формат строки в файле: 'ip_adress:username:password:name of server' (имя - произвольное):comment (не обязательно)\nПример правильной строки: '172.16.0.0:myName:myPass:Тестовый сервер: Это для примера'\nДвоеточие является  разделителем. Допускаются пустые строки, а так же комментарии"
        self.infoText2 = "\nКомментарий всегда должен начинаться с 'comment:'. Пример: 'comment: мой комментарий'"

    def setDEFAULT(self):
        self.sshport = self.DEFAULT_sshport
        self.listParams = self.DEFAULT_listParams

    def katprint(self, text):
        if hasattr(self, 'cons'):
            self.cons["state"] = "normal"
            self.cons.insert(END,text + "\n")
            self.cons["state"] = "disabled"
            self.cons.yview(END)
            self.root.update()
        if self.logging:
            print(text, file = self.logfile)
            self.logfile.close()
            self.logfile = open(self.logfileName,"a")

    def error_window(self, string):
        self.katprint("\n[ERROR] {}".format(string))        

        root = Tk()
        root.title("ERROR")
        root.protocol('WM_DELETE_WINDOW', self.error_action)
        root.resizable(width=False, height=False)
        Label(root, bg="red", text=string, anchor="nw", justify=LEFT, font=("Verdana", 12, "bold")).pack(side=TOP, padx=10, pady=10)
        Button(root, text="Ок", width=20, height=2, bd=4, bg='#C0C0C0', font=("Verdana", 15, "bold"), command=self.error_action).pack(side=BOTTOM, padx=10, pady=10)
        self.root.tkraise()
        root.tkraise()
        root.mainloop()

    def error_action(self):
        if self.logging:
            self.logfile.close()
        sys.exit(0)

    def info_window(self, string, params):
        self.katprint("\n[INFO] {}\n".format(string))

        root = Tk()
        root.title("INFO")
        root.resizable(width=False, height=False)
        Label(root, bg="lightgreen", text=string, anchor="nw", font=("Verdana", 12), justify=LEFT).pack(side=TOP, padx=10, pady=10)
        Button(root, text="Ок", width=20, height=1, bd=4, bg='#C0C0C0', font=("Verdana", 15, "bold"), command = lambda: self.info_action(root, params)).pack(side=BOTTOM, padx=10, pady=10)
        root.mainloop()
    def info_action(self, root, params):
        root.destroy()
        root.quit()
        if params == "enableAllButtons":
            self.buttonsActivate("enable")
    
    def confirmExit_window(self, params):
        if params == "childWindow":
            string1 = "Вы нажали красный крест. Вы уверенны, что хотите закрыть это окно?"
            string2 = "ДА, ЗАКРЫТЬ"
            string3 = "\n[CLOSE] Нажат красный крест закрытия дочернего окна программы\n"
        else:
            string1 = "Вы нажали красный крест. Вы уверенны, что хотите закрыть программу?\n\nЕсли вы закроете программу в процесссе выполнения операции, может произойти сбой!"
            string2 = "ДА, ВЫЙТИ"
            string3 = "\n[EXIT] Нажат красный крест для выхода из программы\n"
        
        self.katprint(string3)

        root = Tk()
        root.title("ВЫХОД")
        root.protocol('WM_DELETE_WINDOW', lambda: self.confirmExit_action(0, root, params))
        root.resizable(width=False, height=False)
        Label(root, bg="red", text = string1, font=("Verdana", 12, "bold")).pack(side=TOP, padx=10, pady=10, fill=BOTH)
        Button(root, text="НЕТ, ПРОДОЛЖИТЬ", width=30, height=1, bd=4, bg='#C0C0C0', font=("Verdana", 15, "bold"), command = lambda: self.confirmExit_action(0, root, params)).pack(side=LEFT, padx=10, pady=10) # LEFT BUTTON
        Button(root, text= string2, width=30, height=1, bd=4, bg='#C0C0C0', font=("Verdana", 15, "bold"), command = lambda: self.confirmExit_action(1, root, params)).pack(side=RIGHT, padx=10, pady=10) # RIGHT BUTTON
        root.mainloop()
    def confirmExit_action(self, mode, root, params):
        if mode == 0:
            if params == "childWindow":
                self.katprint("\n[CLOSE] Закрытие дочернего окна отменено\n")
            else:
                self.katprint("\n[EXIT] Выход из программы отменен\n")

            root.destroy()
            root.quit()
        elif mode == 1:
            if params == "childWindow":
                root.destroy()
                root.quit()
                self.root.childWindow.destroy()
                self.buttonsActivate("enable")

                self.katprint("\n[CLOSE] Дочернее окно программы закрыто\n")
            else:
                self.katprint("\n[EXIT] Выход из программы подтвержден\n")
                
                self.error_action()

    # Модифицируемое меню с двумя кнопками и текстом
    def twoButtons_window(self, header, info, leftButtonText, rightButtonText, leftButtonAction, rightButtonAction, params):
        root = Toplevel(self.root)
        root.title(header)
        root.resizable(width=False, height=False)
        Label(root, text=info, anchor="nw", font=("Verdana", 10, "bold"), justify=LEFT).pack(side=TOP, padx=10, pady=10)
        Button(root, text=leftButtonText, width=18, height=1, bd=4, font=("Verdana", 12, "bold"), bg='#C0C0C0', command= lambda: self.twoButtons_action(leftButtonAction, root, params)).pack(side=LEFT, padx=10, pady=10) # LEFT BUTTON
        Button(root, text=rightButtonText, width=18, height=1, bd=4, font=("Verdana", 12, "bold"), bg='#C0C0C0', command= lambda: self.twoButtons_action(rightButtonAction, root, params)).pack(side=RIGHT, padx=10, pady=10) # RIGHT BUTTON
        root.mainloop()
    def twoButtons_action(self, mode, root, params):
        if mode == 0:
            if self.logging:
                self.logfile.close()
            exit(0)
        elif mode == 1:
            root.destroy()
            root.quit()
        elif mode == 2:
            root.destroy()
            root.quit()
            self.plCheck(params)
        # Старт передачи файлов
        elif mode == 3:
            root.destroy()
            root.quit()
            self.filesTransfer_start(params)
        # Старт выполнения команд
        elif mode == 4:
            root.destroy()
            root.quit()
            self.commandsExec_start(params)

    def ListboxAllSelect(self, event):
        widget = event.widget
        try:
            selection=widget.curselection()
            self.listAll_selectionIndex = int(selection[0])
        except:
            raise

    def ListboxActiveSelect(self, event):
        if 0 < len(self.selected_players):
            widget = event.widget
            try:
                selection=widget.curselection()
                self.listActive_selectionIndex = int(selection[0])
            except:
                raise

    # Действия кнопок выбора плееров
    def listsUpdate(self, mode):
        if mode == 0:
            if hasattr(self, 'listAll_selectionIndex'):
                if not (self.listAll_selectionIndex in self.selected_players):
                    self.selected_players.append(self.listAll_selectionIndex)
                    self.listsRebuild()

        elif mode == 1:
            if hasattr(self, 'listActive_selectionIndex'):
                if self.listActive_selectionIndex < len(self.selected_players):
                    del(self.selected_players[self.listActive_selectionIndex])
                    self.listsRebuild()

        elif mode == 2:
            self.selected_players = []
            for idx, x in enumerate(self.players):
                self.selected_players.append(idx)
            self.listsRebuild()

        elif mode == 3:
            self.selected_players = []
            self.listsRebuild()
            
    # Полное перестроение списка всех плееров и списка выбранных    
    def listsRebuild(self):
        self.listAll.delete(0,END)
        for idx, x in enumerate(self.players):
            if idx in self.selected_players:
                self.listAll.insert(END, " {0}) ------ ДОБАВЛЕНО ------".format(idx + 1))
            else:
                 self.listAll.insert( END, " {0}) \"{1}\" - {2}".format(idx + 1, x[3], x[0]) )
        self.listActive.delete(0,END)
        if 0 < len(self.selected_players):
            for idx, a in enumerate(self.selected_players):
                self.listActive.insert(END," {0}) \"{1}\" - {2}".format(idx + 1, self.players[a][3], self.players[a][0]))
                idx += 1
        
        self.listActive.yview(END)
        self.root.labelCountAll["text"] = "Количество найденных элементов: {}".format(len(self.players))
        self.root.labelCountActive["text"] = "Количество выбранных элементов: {}".format(len(self.selected_players))

    # Управляющая функция прогрессбаром
    def progressbarControl(self, mode, root, params):
        if mode == "init":
            root.config(sliderlength=0, bg="#00FF00", troughcolor="#FF0000")
        elif mode == "set":
            setValue = params[0]
            maxValue = params[1]

            self.root.update()
            root["sliderlength"] = round(root.winfo_width() * (setValue / maxValue))
        elif mode == "disable":
            root.config(sliderlength=0, bg="#DCDCDC", troughcolor="#DCDCDC")

    def checkLabelControl(self, mode, root, params):
        if mode == "none1":
            root["text"]   = "Проверка доступности машин не запущена..."
        elif mode == "set1":
            root["text"]   = "Проверено: {1} из {0} || Доступно: {2} из {0} || Нет доступа: {3} из {0} || Режим: {4}".format( params[0], params[1], params[2], params[3], params[4])
        elif mode == "none2":
            root["text"]   = "Операция не запущена..."
        elif mode == "set2":
            root["text"]   = "Передано: {0} из {1} {2} || Файл: '{3}'".format( params[0], params[1], params[2], params[3])
        elif mode == "set3":
            root["text"]   = "Завершено: {1} из {0} || Всё успешно: {2} из {0} || Нет соединения: {3} из {0} || Связь, но ошибки: {4} из {0}|| Режим: {5}".format( params[0], params[1], params[2], params[3], params[4], params[5])
        elif mode == "set4":
            root["text"]   = "Выполнено: {0} из {1} команд || Машина: '{2}'".format( params[0], params[1], params[2])

    def buttonsActivate(self, mode):
        if mode == "enable":
            mode = NORMAL
        elif mode == "disable":
            mode = DISABLED
        else:
            return None

        for x in [self.root.button_lists0, self.root.button_lists1, self.root.button_lists2, self.root.button_lists3, self.root.button_checkPing, self.root.button_checkSSH, self.root.button_actionF, self.root.button_actionC, self.head_settingsButton]:
                x["state"] = mode

    # Проверка доступности плееров: по SSH (быстро и медленно)
    def plCheck(self, mode):
        if (mode == 0 or mode == 1):
            plCount                         = len(self.selected_players)
            plsBadArr                       = []
            if mode == 0:
                plsmode                     = "SSH (без паролей, быстро)"
            else:
                plsmode                     = "SSH (с паролями, медленно)"

            if 0 == len(self.selected_players):
                self.info_window("Не выбрана ни одина машина, проверка по {} невозможна".format(plsmode), None)
                return
            self.katprint("\n===> Начата проверка доступности по {0} на порт {1}. Будет проверено машин: {2}".format(plsmode, self.sshport, len(self.selected_players)))

            self.buttonsActivate("disable")
            self.checkLabelControl("set1", self.root.label_check, [plCount, 0, 0, 0, plsmode])
            self.progressbarControl("init", self.root.progressbar, None)
            self.root.update()

            if mode == 1:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


            for idx, a in enumerate(self.selected_players):
                try:
                    if mode == 0:
                        ssh = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        ssh.connect((self.players[a][0], self.sshport))
                    else:
                        ssh.connect(hostname=self.players[a][0], username=self.players[a][1], password=self.players[a][2], port=self.sshport)
                    self.katprint("> {0}/{1}) {2} | {3} - доступ ЕСТЬ".format(idx + 1, plCount, self.players[a][3], self.players[a][0]))
                except:
                    plsBadArr.append(a)
                    self.katprint("> {0}/{1}) {2} | {3} - доступ __ОШИБКА__".format(idx + 1, plCount, self.players[a][3], self.players[a][0]))
                
                self.checkLabelControl("set1", self.root.label_check, [plCount, idx + 1, (idx + 1) - len(plsBadArr), len(plsBadArr), plsmode])
                self.progressbarControl("set", self.root.progressbar, [idx + 1, len(self.selected_players )])
                self.root.update()

                try:
                    ssh.close()
                except:
                    None



            self.katprint("\n> Проверка завершена\n> Проверено: {0} || Доступно: {1} из {0} || Нет доступа: {2} из {0} || Режим: {3}\n".format(plCount, len(self.selected_players) - len(plsBadArr), len(plsBadArr), plsmode))
            if len(plsBadArr) > 0:
                self.katprint("> Ошибки возникли при проверке следующих машин:\n")
                for idx, a in enumerate(plsBadArr):
                    self.katprint("> {0}) {1} | {2}".format(idx + 1, self.players[a][3], self.players[a][0]))
                self.katprint("\n")
            self.progressbarControl("disable", self.root.progressbar, None)
            self.checkLabelControl("none1", self.root.label_check, None)
            self.buttonsActivate("enable")
    
    def save_params(self):             
        self.katprint("===> Попытка создать или перезаписать файл настроек '{}'...".format(self.settingsFileName))
        try:
            settingsfile = open(self.settingsFileName,"w")
            self.katprint("> Файл настроек успешно открыт для записи")
        except:
            self.info_window("Возникла ошибка при попытке открыть для записи/перезаписи файл настроек '{}'\nВозможно, у пользователя нет прав для его создания, либо, этот файл уже задействован каким-либо процессом\n\n> Сохранение настроек в файл отменено".format(self.settingsFileName), None)
            return

        self.katprint("> Сохранение параметров в открытый файл...")
        try:
            print("SSHport={}".format(self.sshport), file = settingsfile)
            print("listParams={}".format(self.listParams), file = settingsfile)
        except:
            self.info_window("При записи параметров возникла непредвиденная ошибка...\nСбой сохранения\n\nВозможно, в процессе сохранения у пользователя пропали права на запись в этот файл, либо он занят другим процессом", None)
            try:
                settingsfile.close()
            except:
                self.info_window("При попытке закрыть файл с настройками возникла непредвиденная ошибка...\nСбой сохранения\n\nВозможно, в процессе сохранения у пользователя пропали права на запись в этот файл, либо он занят другим процессом", None)
            return

        try:
            settingsfile.close()
        except:
            self.info_window("При попытке закрыть файл с настройками возникла непредвиденная ошибка...\nСбой сохранения\n\nВозможно, в процессе сохранения у пользователя пропали права на запись в этот файл, либо он занят другим процессом", None)
            return
        self.katprint("> Сохранение параметров в файл настроек успешно завершено, файл закрыт\n")

    # Окно параметров
    def settings_window(self, params):
        self.buttonsActivate("disable")
        self.katprint("===> Открыто дочернее окно общих настроек\n")

        def cancel():
            self.buttonsActivate("enable")
            root.destroy()
            root.quit()
            self.katprint("> Нажата кнопка отмены - новые настройки применены не будут, окно параметров закрыто")

        def confirm(mode):
            if mode == "normal":
                self.katprint("===> Нажата кнопка применения изменений - начата проверка значений...")
            elif mode == "child":
                self.katprint("===> Нажата кнопка применения и сохранения изменений в файл - начата проверка значений...")

            # ===>>> SSH-port
            temp                        = -1
            try:
                temp                    = int(root.sshPort.get())
                self.katprint("> Параметр \"Порт для SSH-подключений\" успешно установлен на значение '{}'".format(temp))
            except:
                self.info_window("Параметр \"Порт для SSH-подключений\" задан некорретно!\nПорт должен являться целым положительным числом\n\nТекущее значение: '{}'".format(root.sshPort.get()), None)
                self.katprint("> Применение параметров частично не выполнено\n")
                return False
            if temp < 0:
                self.info_window("Параметр \"Порт для SSH-подключений\" задан некорретно!\nПорт должен являться целым положительным числом\n\nТекущее значение: '{}'".format(temp), None)
                self.katprint("> Параметр \"Порт для SSH-подключений\" сброшен на исходное значение: '{}'\n> Применение параметров частично не выполнено\n".format(self.sshport))
                return False
            self.sshport                = temp
            # <<<=== SSH-port

            self.katprint("\n> Применение параметров успешно завершено\n")
            return True

        def save():
            if not confirm("child"):
                self.katprint("> При применении некоторых параметров возник сбой, сохранение в файл отменено\n")
                return   
            self.save_params()


        root                                = Toplevel(self.root)
        self.root.childWindow               = root
        root.title("Настройки")
        root.geometry("+100+50")
        root.resizable(width=False, height=False)
        root.protocol('WM_DELETE_WINDOW', lambda: self.confirmExit_window("childWindow"))

        root_frame                          = Frame(root, highlightcolor="#FF0000", highlightbackground="#FF0000", highlightthickness=2)
        root_frame.grid                     (padx=10, pady=10)

        Button                              (root_frame, text="Настройка списка машин...", command= lambda: self.listSettings_window(root), bg='#C0C0C0', bd=4, font=("Verdana", 10, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="we")

        port_frame                          = Frame(root_frame)
        port_frame.grid                     (row=1, column=0, pady=5, padx=10, sticky="w")
        Label                               (port_frame, text="Номер порта для SSH-подключения (по умолчанию: 22):", font=("Verdana", 10, "bold")).grid(row=0, column=0, sticky="w")
        root.sshPort                        = StringVar()
        root.sshPort.set                    (str(self.sshport))
        Entry                               (port_frame, width=3, textvariable=root.sshPort, bg='#008000', fg='#FFFFFF', highlightcolor="#000000", highlightbackground="#000000", highlightthickness=1, font=("Verdana", 10, "bold")).grid(row=0, column=1, sticky="w")

        Frame                               (root_frame, highlightcolor="black", highlightbackground="black", highlightthickness=1).grid(row=2, column=0, pady=5, padx=10, sticky="we") # разделительная черта

        actions_buttons_frame               = Frame(root_frame)
        actions_buttons_frame.grid          (row=3, column=0, pady=5, padx=10, sticky="we")
        Button                              (actions_buttons_frame, text="Отмена", command=cancel, bg='#C0C0C0', bd=4, font=("Verdana", 10, "bold")).grid(row=0, column=0, pady=5, sticky="w")
        Label                               (actions_buttons_frame, width=40).grid(row=0, column=1, pady=5)
        b2_frame                            = Frame(actions_buttons_frame)
        b2_frame.grid                       (row=0, column=2, sticky="e")
        Button                              (b2_frame, text="Применить (только для этой сессии)", command= lambda: confirm("normal"), width=40, bg='#C0C0C0', bd=4, font=("Verdana", 10, "bold")).grid(row=0, column=0, padx=20, pady=5, sticky="e")
        Button                              (b2_frame, text="Сохранить (с записью в файл)", command=save, width=40, bg='#C0C0C0', bd=4, font=("Verdana", 10, "bold")).grid(row=0, column=1, pady=5, sticky="e")

        root.mainloop()
    
    # Окно параметров списка машин
    def listSettings_window(self, params):
        if params != None:
            params.destroy()
            params.quit()

        self.buttonsActivate("disable")
        self.katprint("===> Открыто дочернее окно настроек списка машин\n")

        def back():
            root.destroy()
            root.quit()
            self.katprint("> Нажата кнопка возврата - новые настройки применены не будут, возврат в окно основных настроек")
            self.settings_window(None)

        def confirm():
            entry                               = root.selectedMode_frame.FileEntry.get()
            if ((entry == '') or entry.isspace()):
                self.info_window("Путь к файлу со списком машин не может быть пустым", None)
                return False

            self.listParams[1] = entry
            self.katprint("Обновлено значение файла машин для данной сессии. Новое значение: '{}'\n".format(entry))

            return True
            
        def save():           
            if not confirm():
                self.katprint("> При применении некоторых параметров возник сбой, сохранение в файл отменено\n")
                return
            self.save_params()

        def listRenew():
            self.katprint("===> Инициализирована пересборка списка машин из файла - поиск файла со списком машин...")
            try:
                filePlayers = open(self.listParams[1], 'r')
            except:
                self.info_window("Ошибка открытия файла списка машин\nПроверьте наличие файла '{}', а также его доступность\nВозможно, у пользователя нет прав на чтение файла".format(self.listParams[1]), None)
                try:
                    filePlayers.close()
                except:
                    pass
                return

            temp_array      = []
            self.katprint("> Файл '{}' успешно открыт\n\n===> Попытка чтения списка машин...".format(self.listParams[1]))
            with filePlayers as file:
                for line in file:
                    if not ((line == '') or line.isspace()):
                        line = line.rstrip('\n').split(':')
                        if line [0] != "comment":
                            if len(line) < 4:
                                self.info_window("Ошибка чтения строки \" {0} \" файла '{1}'\n\n{2}".format(line, self.listParams[1], self.infoText1), None)
                                return
                            temp_array.append([line[0], line[1], line[2], line[3]]) # 0 - IP адрес, 1 - имя пользователя, 2 - пароль, 3 - имя плеера
            try:
                filePlayers.close()
            except:
                pass

            if len(temp_array) == 0:
                self.info_window("В файле '{0}' не найдено необходимых записей.\n{1}".format(self.listParams[1], self.infoText1 + self.infoText2), None)
                return
            else:
                self.katprint( "> В файле '{0}' найдено данных: {1}\n".format(self.listParams[1], len(self.players)) )

            self.players    = temp_array
            self.katprint("> Список машин успешно загружен из файла.\n> Обновление графического интерфейса...\n")
            self.listsRebuild()
            self.katprint("> Графический интерфейс обновлен успешно\n> Пересборка списка завершена!")


        # Создание индивидуального меню настроек для каждого режима
        def menu_create(root):
            root.selectedMode_frame.destroy()
            root.selectedMode_frame             = Frame(modes_frame)
            root.selectedMode_frame.grid        (row=0, column=3, pady=5, sticky="nswe")
            root.selectedMode_frame.grid_columnconfigure    (0, weight=1)
            # Файл
            if root.modes_var.get() == 0:
                Label(root.selectedMode_frame, text="Выгрузка из файла:").grid(row=0, column=0)

                root.selectedMode_frame.grid_rowconfigure    (1, minsize=25)
                Label                           (root.selectedMode_frame, justify=LEFT, text="Путь может быть абсолютным (пример: 'C:\\zDistr\myFile.txt'), либо относительным от корневой папки программы (пример: 'myFolder\\myFile.txt', либо 'myFile.txt')").grid(row=2, column=0, sticky="w")
                Label                           (root.selectedMode_frame, text="По умолчанию - файл с именем 'players.txt' создается в корневом каталоге программы (значение параметра: 'players.txt')").grid(row=3, column=0, sticky="w")
                Label                           (root.selectedMode_frame, justify=LEFT, text="Чтобы после изменения файла получить из него новый список машин - сначала примените или сохраните изменения, после чего выполняйте пересборку\n\nНиже указывается путь к файлу:").grid(row=4, column=0, sticky="w")
                fileEntry                       = StringVar()
                fileEntry.set                   (self.listParams[1])
                root.selectedMode_frame.FileEntry               = Entry(root.selectedMode_frame, width=50, textvariable=fileEntry, bg='#008000', fg='#FFFFFF', highlightcolor="#000000", highlightbackground="#000000", highlightthickness=1, font=("Verdana", 10, "bold"))
                root.selectedMode_frame.FileEntry.grid          (row=5, column=0, sticky="we")
                root.selectedMode_frame.grid_rowconfigure    (6, weight=1)
                Button                          (root.selectedMode_frame, text="Пересобрать список машин из указанного файла", command=listRenew, bg='#C0C0C0', bd=4, font=("Verdana", 10, "bold")).grid(row=7, column=0, sticky="we")

            # SQL-сервер
            elif root.modes_var.get() == 1:
                Label(root.selectedMode_frame, text="Режим соединения с SQL-сервером в разработке...").grid(row=0, column=0)





        root                                = Toplevel(self.root)
        root.menu_structures                = []
        self.root.childWindow               = root
        root.title("Настройки списка машин")
        root.geometry("+100+50")
        root.resizable(width=False, height=False)
        root.protocol('WM_DELETE_WINDOW', lambda: self.confirmExit_window("childWindow"))

        root_frame                          = Frame(root, highlightcolor="#C71585", highlightbackground="#C71585", highlightthickness=2)
        root_frame.grid                     (padx=10, pady=10)




        # Общая рамка:
        modes_frame                         = Frame(root_frame)
        modes_frame.grid                    (row=0, column=0, padx=10, pady=10, sticky="we")

        # Кнопки выбора режима
        modes_radio_frame                   = Frame(modes_frame)
        modes_radio_frame.grid              (row=0, column=0, pady=5, padx=10, sticky="n")
        Label                               (modes_radio_frame, text="Выбор режима чтения списка машин:").grid(row=0, sticky="w")
        root.modes_var                      = IntVar()
        root.modes_var.set                  (self.listParams[0])
        radio0                              = Radiobutton(modes_radio_frame, value = 0, text = "Из файла", variable=root.modes_var, command = lambda: menu_create(root), width=30, activeforeground="#006400", activebackground="#4682B4", bg="#DC143C", selectcolor="#9ACD32",  bd=5, indicatoron=False)
        radio1                              = Radiobutton(modes_radio_frame, value = 1, text = "С SQL-сервера", variable=root.modes_var, command = lambda: menu_create(root), width=30, activeforeground="#006400", activebackground="#4682B4", bg="#DC143C", selectcolor="#9ACD32", bd=5, indicatoron=False)

        radio0.grid                         (row=1, column=0, pady=5, sticky="we")
        radio1.grid                         (row=2, column=0, pady=5, sticky="we")

        # Вертикальный разделитель
        Frame                               (modes_frame, height=300, highlightcolor="black", highlightbackground="black", highlightthickness=1).grid(row=0, column=1, pady=5, padx=10, sticky="ns") # разделительная черта


        # Меню выбранного режима
        modes_frame.grid_columnconfigure    (2, minsize=10)
        modes_frame.grid_columnconfigure    (3, weight=1)
        root.selectedMode_frame                  = Frame(modes_frame)
        root.selectedMode_frame.grid             (row=0, column=3, pady=5, padx=10, sticky="nswe")




        Frame                               (root_frame, highlightcolor="black", highlightbackground="black", highlightthickness=1).grid(row=1, column=0, pady=5, padx=10, sticky="we") # разделительная черта

        actions_buttons_frame               = Frame(root_frame)
        actions_buttons_frame.grid          (row=2, column=0, pady=5, padx=10, sticky="we")
        Button                              (actions_buttons_frame, text="Назад", command=back, bg='#C0C0C0', bd=4, font=("Verdana", 10, "bold")).grid(row=0, column=0, pady=5, sticky="w")
        Label                               (actions_buttons_frame, width=60).grid(row=0, column=1, pady=5)
        b2_frame                            = Frame(actions_buttons_frame)
        b2_frame.grid                       (row=0, column=2, sticky="e")
        Button                              (b2_frame, text="Применить (только для этой сессии)", command=confirm, width=40, bg='#C0C0C0', bd=4, font=("Verdana", 10, "bold")).grid(row=0, column=0, padx=20, pady=5, sticky="e")
        Button                              (b2_frame, text="Сохранить (с записью в файл)", command=save, width=40, bg='#C0C0C0', bd=4, font=("Verdana", 10, "bold")).grid(row=0, column=1, pady=5, sticky="e")

        menu_create(root)
        root.mainloop()

    # Окна дейсвтий: передача файлов и выполнение команд
    def plAct_window(self, mode):
        self.buttonsActivate("disable")
        self.root.update()
        if 0 == len(self.selected_players):
                self.info_window("Не выбрана ни одина машина, запрашиваемое действие выполнить невозможно", "enableAllButtons")
                return None
        
        if mode == 0:
            self.katprint("===> Открыто дочернее окно выбора файлов для передачи\n")

            root = Toplevel(self.root)
            self.root.childWindow           = root
            root.title("Передача файлов")
            root.geometry("+100+50")
            root.protocol('WM_DELETE_WINDOW', lambda: self.confirmExit_window("childWindow"))
            root.resizable(width=False, height=False)
            root_frame                      = Frame(root, highlightcolor="#008000", highlightbackground="#008000", highlightthickness=2)
            root_frame.grid                 (padx=10, pady=10)

            # radiobutton function
            def radioChange(mode):
                if mode == 2:
                    root.customDirLabel["state"] = NORMAL
                    root.destDir            = "CUSTOM"
                else:
                    if root.customDirLabel["state"] == NORMAL:
                        root.customDirLabel["state"] = DISABLED

                    if mode == 0:
                        root.destDir        = "~/kattemp"
                    elif mode == 1:
                        root.destDir        = "~/media"
                    else:
                        return None

            # Edit file list Function
            def editFilesAction(mode):
                if mode == 0:
                    stringFiles             = askopenfilenames(parent=root, title='Выберите файлы')
                    for idx, x in enumerate(stringFiles):
                        self.array_files.append(x)
                        root.listFiles.insert(END, " {0}) {1}".format(len(self.array_files), x))
                elif mode == 1:
                    del(self.array_files[len(self.array_files) - 1])
                    root.listFiles.delete(END, END)
                elif mode == 2:
                    self.array_files        = []
                    root.listFiles.delete(0, END)
                else:
                    return None

                root.listFiles.yview(END)
                root.labelCountFiles["text"]= "Количество выбранных файлов: {}".format(len(self.array_files))

            def START():
                if len(self.array_files) == 0:
                    self.info_window("Не выбран ни один файл для передачи", None)

                if root.destDir == "CUSTOM":
                    self.destDir            = root.customDirLabel.get()
                else:
                    self.destDir            = root.destDir

                if ( (self.destDir == '') or self.destDir.isspace() ):
                    self.info_window("В качестве целевой папки выбран собственный вариант расположения,\nОднако, путь к цели не указан.\nПроверьте поле ввода.", None)
                    return None

                self.clearDestDir           = root.clearDestDir.get()

                if self.clearDestDir:
                    string                  = "ДА"
                else:
                    string                  = "НЕТ"

                string2                     = "Выбрано файлов для передачи: {0}\nВыбранно целевых машин для передачи: {1}\nПуть целевой папки: \"{2}\"\nОчистка целевой папки: {3}\n\nПередача файлов может занять длительное время.\n\n".format(len(self.array_files), len(self.selected_players), self.destDir, string)
                self.katprint(string2)
                self.twoButtons_window("Передача {} файлов".format(len(self.array_files)), "{0}НАЧАТЬ ПЕРЕДАЧУ {1} ФАЙЛОВ НА {2} МАШИН?".format(string2, len(self.array_files), len(self.selected_players)), "Нет", "Да", 1, 3, root)
                    
                

            #/////////// Параметры
            targetDirMode                   = IntVar()
            targetDirMode.set               (0)
            self.customDestDir              = StringVar()
            root.clearDestDir               = BooleanVar()
            try:
                root.clearDestDir.set       (self.clearDestDir)
            except:
                root.clearDestDir.set       (0)
            root.destDir                    = "~/kattemp"
            paramsFrame                     = Frame(root_frame, highlightcolor="#000000", highlightbackground="#000000", highlightthickness=1)
            radio0                          = Radiobutton(paramsFrame, value = 0, text = "~/kattemp", variable=targetDirMode, command = lambda: radioChange(0), activeforeground="#006400")
            radio1                          = Radiobutton(paramsFrame, value = 1, text = "~/media", variable=targetDirMode, command = lambda: radioChange(1), activeforeground="#006400")
            radio2                          = Radiobutton(paramsFrame, value = 2, text = "Свой вариант:", variable=targetDirMode, command = lambda: radioChange(2), activeforeground="#006400")
            root.customDirLabel             = Entry(paramsFrame, state = DISABLED, textvariable=self.customDestDir, width = 35, bg='#008000', fg='#FFFFFF', highlightcolor="#000000", highlightbackground="#000000", highlightthickness=1, text = "Введите свой путь назначения сюда")
            root.clearDestDirBox            = Checkbutton(paramsFrame, text = "Удалить всё из целевой папки перед передачей", variable = root.clearDestDir, offvalue = 0, onvalue = 1)


            paramsFrame.grid                (row = 0, padx=10, pady=10, sticky="we")
            radio0.grid                     (row = 0, column = 0, padx=10, pady=5, sticky = "w")
            radio1.grid                     (row = 1, column = 0, padx=10, pady=5, sticky = "w")
            radio2.grid                     (row = 2, column = 0, padx=10, pady=5, sticky = "w")
            root.customDirLabel.grid        (row = 2, column = 1, padx=10, pady=5, sticky = "w")
            root.clearDestDirBox.grid       (row = 1, column = 2, padx=10, pady=5)
            #\
            # !!!!!!!!!!! ВЫБОР ФАЙЛОВ ДЛЯ ПЕРЕДАЧИ !!!!!!!!!!!
            selectFilesFrame                = Frame(root_frame)
            #/////////// Список выбранных файлов
            listFiles                       = Frame(selectFilesFrame, highlightcolor="black", highlightbackground="black", highlightthickness=1)
            Label                           (listFiles, text = "Выбранные файлы:", anchor="w", bg='#808080').grid(row=0, sticky="we")
            root.labelCountFiles            = Label(listFiles, text = "Количество выбранных файлов: {}".format(len(self.array_files)), anchor="w", bg='#00FF7F')
            root.listFiles                  = Listbox(listFiles, selectmode=SINGLE, exportselection=False, height = 30, width = 80, highlightcolor="black", highlightbackground="black", highlightthickness=1)
            listFiles_scroll2               = Scrollbar(listFiles, orient='horizontal', command=root.listFiles.xview)
            listFiles_scroll                = Scrollbar(listFiles, orient='vertical', command=root.listFiles.yview)


            root.listFiles['xscrollcommand']= listFiles_scroll2.set
            root.listFiles['yscrollcommand']= listFiles_scroll.set

            root.listFiles.grid             (row=1)
            listFiles_scroll.grid           (row=1, column=1, sticky='ns')
            listFiles_scroll2.grid          (row=2, column=0, sticky='we', columnspan=2)
            root.labelCountFiles.grid       (row=3, sticky="we", columnspan=2)
            listFiles.grid                  (row=0, column=0, padx=10, pady=10, sticky="w", rowspan=2)

            for idx, x in enumerate(self.array_files):
                root.listFiles.insert(END, " {0}) \"{1}\"".format(idx + 1, x))
            #\
            #/////////// Кнопки редактирования списка файлов
            editFileButtonsFrame            = Frame(selectFilesFrame)
            Button                          (editFileButtonsFrame, text = "Добавить файлы" , width=24, height=2, bd=4, command = lambda: editFilesAction(0), bg='#C0C0C0', font=("Verdana", 10, "bold")).grid(row=0, padx=10, pady=5)
            Button                          (editFileButtonsFrame, text = "Удалить последний файл" , width=24, height=2, bd=4, command = lambda: editFilesAction(1), bg='#C0C0C0', font=("Verdana", 10, "bold")).grid(row=1, padx=10, pady=5)
            Button                          (editFileButtonsFrame, text = "Удалить все файлы" , width=24, height=2, bd=4, command = lambda: editFilesAction(2), bg='#C0C0C0', font=("Verdana", 10, "bold")).grid(row=2, padx=10, pady=5)

            editFileButtonsFrame.grid       (row=0, column=1, sticky="w")
            #\ 
            #/////////// Кнопка СТАРТ
            Button                          (selectFilesFrame, text = "СТАРТ" , width=8, height=1, bd=4, command = START, bg='#C0C0C0', font=("Verdana", 30, "bold")).grid(row=1, column=1, padx=10, pady=10, sticky="s")
            #\

            selectFilesFrame.grid           (row=1, column=0, sticky="w")
            # \  ВЫБОР ФАЙЛОВ ДЛЯ ПЕРЕДАЧИ \ 
            root.mainloop()
#


        elif mode == 1:
            self.katprint("===> Открыто дочернее окно ввода команд для выполнения\n")

            root                            = Toplevel(self.root)
            self.root.childWindow = root
            root.title("Выполнение команд")
            root.geometry("+100+50")
            root.protocol('WM_DELETE_WINDOW', lambda: self.confirmExit_window("childWindow"))
            root.resizable(width=False, height=False)
            root_frame                      = Frame(root, highlightcolor="#FFA500", highlightbackground="#FFA500", highlightthickness=2)
            root_frame.grid                 (padx=10, pady=10)

            # Дейсвтия кнопок редактирвоания списка команд
            def editCmdsAction(mode):
                if mode == 0:
                    entry                       = root.cmdEntry.get()
                    if ((entry == '') or entry.isspace()):
                        self.info_window("Нельзя добавить пустую команду", None)
                        return
                    self.array_commands.append(entry)
                    editCmdsAction("rebuild")
                elif mode == 1:
                    if len(self.array_commands) == 0:
                        self.info_window("Не введена ни одна команда для удаления последней", None)
                        return
                    del(self.array_commands[len(self.array_commands) - 1])
                    editCmdsAction("rebuild")
                elif mode == 2:
                    self.array_commands         = []
                    editCmdsAction("rebuild")
                elif mode == "rebuild":
                    root.listCmds.delete(0, END)
                    for idx, x in enumerate(self.array_commands):
                        root.listCmds.insert(END, " {0}) \"{1}\"".format(idx + 1, x))
                    root.labelCountCmds["text"]   = "Количество введенных команд: {}".format(len(self.array_commands))
                elif mode == 3:
                    if root.isRouters.get():
                        root.sleepLabel["state"]=NORMAL
                        root.sleepEntry["state"]=NORMAL
                    else:
                        root.sleepLabel["state"]=DISABLED
                        root.sleepEntry["state"]=DISABLED

            def START():
                if len(self.array_commands) == 0:
                    self.info_window("Не введена ни одна команда, начать выполнение невозможно", None)
                    return

                temp                            = -1
                self.isRouters                  = root.isRouters.get()
                if self.isRouters:
                    string                      = "Выбранные элементы ЯВЛЯЮТСЯ роутерами"
                    try:
                        temp                    = int(root.timeSleep.get())
                        string                  = string + "\nВремя ожидания ответа: {} с.".format(temp)
                    except:
                        self.info_window("Установлен флаг, обозначающий что выбранные машины являются роутерами.\nПринцип отправки команд таков, что для получения корректного ответа, порой требуется выждать некоторое время до продолжения\nПоэтому, требутеся указать время ожидания в секундах (ЦЕЛОЕ ПОЛОЖИТЕЛЬНОЕ число, либо 0)\n\nВведенная строка: '{}' не может быть конвертирована в целое число".format(root.timeSleep.get()), None)
                        return
                    if temp < 0:
                        self.info_window("Установлен флаг, обозначающий что выбранные машины являются роутерами.\nПринцип отправки команд таков, что для получения корректного ответа, порой требуется выждать некоторое время до продолжения\nПоэтому, требутеся указать время ожидания в секундах (ЦЕЛОЕ ПОЛОЖИТЕЛЬНОЕ число, либо 0)\n\nВведённое число: '{}' не может быть использовано как время задержки до получения ответа от роутера".format(root.timeSleep.get()), None)
                        return
                    self.routerWaitForAnswerTime= temp
                else:
                    string                      = "Выбранные элементы НЕ являются роутерами"


                string                          = "Введено команд для выполнения: {0}\nВыбранно целевых машин для выполнения: {1}\n{2}\n\nВыполнение введенных команд может занять некоторое время.\n\n".format(len(self.array_commands), len(self.selected_players), string)
                self.katprint(string)
                self.twoButtons_window("Выполнение {} команд".format(len(self.array_commands)), "{0}НАЧАТЬ ВЫПОЛНЕНИЕ {1} КОМАНД НА {2} МАШИНАХ?".format(string, len(self.array_commands), len(self.selected_players)), "Нет", "Да", 1, 4, root)

            #/////////// Список введенных команд
            listCmds                        = Frame(root_frame, highlightcolor="black", highlightbackground="black", highlightthickness=1)
            Label                           (listCmds, text = "Введенные команды:", anchor="w", bg='#808080').grid(row=0, sticky="we")
            root.labelCountCmds             = Label(listCmds, anchor="w", bg='#00FF7F')
            root.listCmds                   = Listbox(listCmds, selectmode=SINGLE, exportselection=False, height = 30, width = 80, highlightcolor="black", highlightbackground="black", highlightthickness=1)
            listCmds_scroll2                = Scrollbar(listCmds, orient='horizontal', command=root.listCmds.xview)
            listCmds_scroll                 = Scrollbar(listCmds, orient='vertical', command=root.listCmds.yview)


            root.listCmds['xscrollcommand'] = listCmds_scroll2.set
            root.listCmds['yscrollcommand'] = listCmds_scroll.set

            root.listCmds.grid              (row=1)
            listCmds_scroll.grid            (row=1, column=1, sticky='ns')
            listCmds_scroll2.grid           (row=2, column=0, sticky='we', columnspan=2)
            root.labelCountCmds.grid        (row=3, sticky="we", columnspan=2)
            listCmds.grid                   (row=0, column=0, padx=10, pady=10, sticky="w", rowspan=2)

            editCmdsAction("rebuild")
            #\
            #/////////// Область редактирования списка команд
            editCommandsFrame               = Frame(root_frame)
            isRoutersFrame                  = Frame(editCommandsFrame)

            root.isRouters                  = BooleanVar()
            try:
                root.isRouters.set          (self.isRouters)
            except:
                root.isRouters.set          (0)

            root.timeSleep                  = StringVar()
            try:
                root.timeSleep.set          (str(self.routerWaitForAnswerTime))
            except:
                root.timeSleep.set          ("3")

            Checkbutton                     (editCommandsFrame, text = "Выбранные ранее машины являются роутерами", command=lambda: editCmdsAction(3), variable = root.isRouters, offvalue = 0, onvalue = 1, bg='#C0C0C0', font=("Verdana", 13)).grid(row=0, pady=5, sticky="w")
            root.sleepLabel                 = Label(isRoutersFrame, text="Время ожидания ответа роутера (с): ", font=("Verdana", 10, "bold"))
            root.sleepEntry                 = Entry(isRoutersFrame, width=3, textvariable=root.timeSleep, bg='#008000', fg='#FFFFFF', highlightcolor="#000000", highlightbackground="#000000", highlightthickness=1, font=("Verdana", 10, "bold"))
            
            root.cmdEntry                   = Entry(editCommandsFrame, width = 35, bg='#008000', fg='#FFFFFF', highlightcolor="#000000", highlightbackground="#000000", highlightthickness=1, font=("Verdana", 10, "bold"))
            Button                          (editCommandsFrame, text = "Добавить введенную команду" , width=30, height=2, bd=4, command = lambda: editCmdsAction(0), bg='#C0C0C0', font=("Verdana", 10, "bold")).grid(row=2, column=3, pady=5, sticky="e")
            Button                          (editCommandsFrame, text = "Удалить последнюю команду" , width=30, height=2, bd=4, command = lambda: editCmdsAction(1), bg='#C0C0C0', font=("Verdana", 10, "bold")).grid(row=2, column=2, padx=10, pady=5, sticky="e")
            Button                          (editCommandsFrame, text = "Удалить все команды" , height=2, bd=4, command = lambda: editCmdsAction(2), bg='#C0C0C0', font=("Verdana", 10, "bold")).grid(row=2, column=0, pady=5, sticky="w")

            root.sleepLabel.grid            (row=0, column=0, padx=10, sticky="e")
            root.sleepEntry.grid            (row=0, column=1)
            root.cmdEntry.grid              (row=1, column=0, sticky="we", columnspan=4)

            editCommandsFrame.grid          (row=0, column=1, padx=10, sticky="we")
            isRoutersFrame.grid             (row=0, column=2, padx=10, sticky="e", columnspan=2)
            #\
            #/////////// Кнопка СТАРТ
            Button                          (editCommandsFrame, text = "СТАРТ" , width=8, height=1, bd=4, command = START, bg='#C0C0C0', font=("Verdana", 30, "bold")).grid(row=3, column=3, pady=90, sticky="e")
            #\

            if self.isRouters:
                root.sleepLabel["state"]=NORMAL
                root.sleepEntry["state"]=NORMAL
            else:
                root.sleepLabel["state"]=DISABLED
                root.sleepEntry["state"]=DISABLED

            root.mainloop()
        else:
            return
        


# ==========================================================================================================================================================================================================
# ======================================================================================== ПЕРЕДАЧА ФАЙЛОВ - РАБОТА ========================================================================================
# ==========================================================================================================================================================================================================
    def filesTransfer_start(self, childRoot):
        self.katprint("===================> НАЧАЛО ПЕРЕДАЧИ ФАЙЛОВ <===================\n\n")

        childRoot.destroy()
        childRoot.quit()
        self.root.protocol('WM_DELETE_WINDOW', lambda: None)

        plCount                             = len(self.selected_players)
        flCount                             = len(self.array_files)
        arrConnectError                     = []
        arrSomethingError                   = []

        self.progressbarControl("init", self.root.progressbar, None)
        self.progressbarControl("init", self.root.progressbar2, None)
        self.checkLabelControl("set2", self.root.label_check, [0, 0, "байт", "Не выбран"])
        self.checkLabelControl("set3", self.root.label_check2, [plCount, 0, 0, 0, 0, "Передача файлов"])
        
        self.root.update()

        def fileTransferProgress(x, y, tFile):
            if y > 1073741824:
                string                      = "Гб"
                integer1                    = x / 1073741824
                integer2                    = y / 1073741824
            elif y > 1048576:
                string                      = "Мб"
                integer1                    = x / 1048576
                integer2                    = y / 1048576
            elif y > 1024:
                string                      = "Кб"
                integer1                    = x / 1024
                integer2                    = y / 1024
            else:
                string                      = "Байт"
                integer1                    = x
                integer2                    = y
            integer1                        = round(integer1, 2)
            integer2                        = round(integer2, 2)
            self.progressbarControl("set", self.root.progressbar, [x, y])
            self.checkLabelControl("set2", self.root.label_check, [integer1, integer2, string, tFile])

        # Цикл обработки плееров и файлов
        for idx, a in enumerate(self.selected_players):
            arrFilesError                   = []
            element                         = self.players[a]
            destPatch                       = self.destDir
            if destPatch[0] == '~':
                destPatch                   = "/home/{0}{1}".format(element[1], destPatch[1:len(destPatch)])
            
            self.katprint("===> [CONNECT] Попытка установки SFTP-соединения с '{0}' по IP-адресу {1} и порту {2}...".format(element[3], element[0], self.sshport))
            try:
                transport = paramiko.Transport((element[0], 22))
                transport.connect(username = element[1], password = element[2])
                sftp = paramiko.SFTPClient.from_transport(transport)
                self.katprint("> [CONNECT] SFTP-соединение выполнено успешно!")
            except:
                self.katprint("> [CONNECT] Установка SFTP-соединения с '{0}' по IP-адресу {1} и порту {2} - __ОШИБКА__\n> Проверьте правильность указанного имени пользователя, пароля, а также доступность устройства\n\n".format(element[3], element[0], self.sshport))
                arrConnectError.append(a)

                self.progressbarControl("set", self.root.progressbar2, [idx + 1, plCount])
                self.checkLabelControl("set3", self.root.label_check2, [plCount, idx + 1, (idx + 1) - len(arrSomethingError) - len(arrConnectError), len(arrConnectError),len(arrSomethingError), "Передача файлов"])
                self.root.update()
                continue
        
            try:
                sftp.chdir(destPatch)
                self.katprint("> Директория '{}' найдена\n".format(destPatch))
            except:
                self.katprint("> Директория '{}' не найдена".format(destPatch))
                try:
                    def mkdir_p(sftp, patch):
                        if patch == '/':
                            sftp.chdir("/")
                            return
                        if patch == '':
                            return
                        dirname, basename = os.path.split(patch.rstrip('/'))
                        try:
                            sftp.chdir(dirname)
                        except:
                            mkdir_p(sftp, dirname)
                        sftp.mkdir(basename)
                        sftp.chdir(basename)
                    
                    mkdir_p(sftp, destPatch)

                    sftp.chdir(destPatch)
                    self.katprint("> Директория '{}' успешно создана\n".format(destPatch))

                except:
                    self.katprint("> Не удалось создать директорию '{0}' - неизвестная ошибка. Возможно, у пользователя '{1}' нет прав на создание директорий по данному пути\n\n".format(destPatch, element[1]))
                    arrSomethingError.append(a)

                    self.progressbarControl("set", self.root.progressbar2, [idx + 1, plCount])
                    self.checkLabelControl("set3", self.root.label_check2, [plCount, idx + 1, (idx + 1) - len(arrSomethingError) - len(arrConnectError), len(arrConnectError),len(arrSomethingError), "Передача файлов"])
                    self.root.update()
                    continue
            
            if self.clearDestDir:
                objects                     = sftp.listdir('.')
                if len(objects) > 0:
                    self.katprint("===> Был выбран параметр \"Очистить целевую папку\", выполняется очистка...")
                
                    def delDirFiles(objects, parent):
                        for x in objects:
                            nextObject          = '{0}/{1}'.format(parent, x)
                            if sftp.lstat(nextObject).st_mode == 16877: # isDir?
                                delDirFiles(sftp.listdir(nextObject), nextObject)
                                try:
                                    sftp.rmdir(nextObject)
                                except:
                                    self.katprint("> При удалении каталога '{0}' произошла ошибка. Возможно, у пользователя '{1}' не достаточно прав для этого, либо целева директория указана некорректно".format(nextObject, element[1]))
                                    if not (a in arrSomethingError):
                                        arrSomethingError.append(a)
                            else:
                                try:
                                    sftp.remove(nextObject)
                                except:
                                    self.katprint("> При удалении файла '{0}' произошла ошибка. Возможно, у пользователя '{1}' не достаточно прав для этого".format(nextObject, element[1]))
                                    if not (a in arrSomethingError):
                                        arrSomethingError.append(a)

                    delDirFiles(objects, destPatch)
                    self.katprint("> Очистка каталога '{}' завершена\n".format(destPatch))
                


                else:
                    self.katprint("===> Был выбран параметр \"Очистить целевую папку\", однако, папка уже пуста.\n")


            for idx2, x in enumerate(self.array_files):
                self.katprint("===> Начало передачи файла '{0}' в каталог '{1}'".format(x, destPatch))
                try:
                    tmp = x
                    sftp.put(x, './{}'.format(os.path.basename(x)), lambda x,y: fileTransferProgress(x, y, tmp))
                    self.katprint("> Файл '{0}' успешно передан в каталог '{1}'\n> Обработано: {2}/{3} || Успешно: {4}/{3} || С ошибками: {5}\n".format(x, destPatch, idx2 + 1, len(self.array_files), (idx2 + 1) - len(arrFilesError), len(arrFilesError)))
                except:
                    arrFilesError.append(x)
                    self.katprint("> __ОШИБКА__ передачи файла '{0}' в каталог '{1}'.\n> Возможно, локальный файл не был найден, либо соединение с удаленным сервером было разорвано\n> Обработано: {2}/{3} || Успешно: {4}/{3} || С ошибками: {5}\n".format(x, destPatch, idx2 + 1, len(self.array_files), (idx2 + 1) - len(arrFilesError), len(arrFilesError)))
                    if not (a in arrSomethingError):
                        arrSomethingError.append(a)
            self.katprint ("\n> Передача файлов для '{0}' с IP-адресом {1} в каталог '{2}' завершена. Успешно передано файлов: {3} из {4}. Ошибок при передаче: {5}\n".format(element[3], element[0], destPatch, len(self.array_files) - len(arrFilesError), len(self.array_files), len(arrFilesError)))
            if len(arrFilesError) > 0:
                self.katprint("> Некоторые файлы не удалось передать в каталог '{0}' от имени пользователя '{1}':".format(destPatch, element[1]))
                for idx, x in enumerate(arrFilesError):
                    self.katprint(" {0}) '{1}'".format(idx + 1, x))
                self.katprint('\n')
            try:
                sftp.close()
            except:
                pass
            self.katprint("> [CONNECT] Соединение с '{0}' | {1} нормально закрыто\n\n".format(element[3], element[0]))
            
            #Обновление общей шкалы
            self.progressbarControl("set", self.root.progressbar2, [idx + 1, plCount])
            self.checkLabelControl("set3", self.root.label_check2, [plCount, idx + 1, (idx + 1) - len(arrSomethingError) - len(arrConnectError), len(arrConnectError),len(arrSomethingError), "Передача файлов"])
            self.root.update()
        
        self.katprint("<===================> ПЕРЕДАЧА ФАЙЛОВ ЗАВЕРШЕНА <===================>\n> Всего обработано машин: {0}\n> Успешно завершено: {1}\n> Нет связи: {2}\n> Есть связь, но возникли какие-либо ошибки: {3}".format(plCount, plCount - len(arrSomethingError) - len(arrConnectError), len(arrConnectError), len(arrSomethingError)))
        
        if len(arrConnectError) > 0:
            self.katprint("\n===> При обработке {0} машин возникла проблема с установкой связи. Стоит проверить лог-файл '{1}', а также убедиться в доступности целей. Список проблемных элементов:".format(len(arrConnectError), self.logfileName))
            for idx, a in enumerate(arrConnectError):
                self.katprint(" {0}) '{1}' с IP-адресом {2}".format(idx + 1, self.players[a][3], self.players[a][0]))

        if len(arrSomethingError) > 0:
            self.katprint("\n===> При обработке {0} машин возникли некоторые ошибки. Стоит проверить лог-файл '{1}'. Список проблемных элементов:".format(len(arrSomethingError), self.logfileName))
            for idx, a in enumerate(arrSomethingError):
                self.katprint(" {0}) '{1}' с IP-адресом {2}".format(idx + 1, self.players[a][3], self.players[a][0]))
        self.katprint("\n\n")

        # Возвращение GUI в нормальное состояние
        self.root.protocol('WM_DELETE_WINDOW', lambda: self.confirmExit_window(None))
        self.progressbarControl("disable", self.root.progressbar, None)
        self.progressbarControl("disable", self.root.progressbar2, None)
        self.checkLabelControl("none1", self.root.label_check, None)
        self.checkLabelControl("none2", self.root.label_check2, None)
        self.buttonsActivate("enable")
        self.root.update()

        





# =========================================================================================================================================================================================================
# ================================================================================== ВЫПОЛНЕНИЕ ЗАДАННЫХ КОМАНД - РАБОТА ==================================================================================
# =========================================================================================================================================================================================================

    def commandsExec_start(self, childRoot):
        self.katprint("===================> НАЧАЛО ВЫПОЛНЕНИЯ КОМАНД <===================\n\n")

        childRoot.destroy()
        childRoot.quit()
        self.root.protocol('WM_DELETE_WINDOW', lambda: None)

        plCount                             = len(self.selected_players)
        comCount                            = len(self.array_commands)
        arrConnectError                     = []
        arrSomethingError                   = []

        self.progressbarControl("init", self.root.progressbar, None)
        self.progressbarControl("init", self.root.progressbar2, None)
        self.checkLabelControl("set4", self.root.label_check, [0, comCount, "None"])
        self.checkLabelControl("set3", self.root.label_check2, [plCount, 0, 0, 0, 0, "Выполнение команд"])
        
        self.root.update()

        ssh                                 = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Цикл обработки плееров и команд
        for idx, a in enumerate(self.selected_players):
            element                         = self.players[a]
            arrСomError                     = []
            
            if self.isRouters:
                self.katprint("===> [CONNECT] Попытка установки SSH-соединения с роутером '{0}' по IP-адресу {1} и порту {2}...".format(element[3], element[0], self.sshport))
            else:
                self.katprint("===> [CONNECT] Попытка установки SSH-соединения с '{0}' по IP-адресу {1} и порту {2}...".format(element[3], element[0], self.sshport))
            try:
                ssh.connect(hostname= element[0], username= element[1], password= element[2], port= self.sshport)
                self.katprint("> [CONNECT] SSH-соединение выполнено успешно!")
            except:
                self.katprint("> [CONNECT] Установка SSH-соединения с '{0}' по IP-адресу {1} и порту {2} - __ОШИБКА__\n> Проверьте правильность указанного имени пользователя, пароля, а также доступность устройства\n\n".format(element[3], element[0], self.sshport))
                arrConnectError.append(a)

                self.progressbarControl("set", self.root.progressbar2, [idx + 1, plCount])
                self.checkLabelControl("set3", self.root.label_check2, [plCount, idx + 1, (idx + 1) - len(arrSomethingError) - len(arrConnectError), len(arrConnectError), len(arrSomethingError), "Выполнение команд"])
                self.root.update()
                continue

            # Передача команд
            self.katprint("===> Начало выполнения {} команд:\n".format(comCount))
            for idx2, x in enumerate(self.array_commands):
                stdin                       = ""
                stdout                      = "ERROR"
                stderr                      = "ERROR"
                self.katprint("===> Выполнение команды '{0}'...".format(x))
                try:
                    if self.isRouters:
                        chan = ssh.invoke_shell()
                        time.sleep(1)
                        chan.send(x + ' \n')
                        time.sleep(self.routerWaitForAnswerTime)
                    else:
                        stdin, stdout, stderr = ssh.exec_command(x)
                except:
                    arrСomError.append(x)
                    self.katprint("> __ОШИБКА__ выполнения команды '{0}'.\n> Возможно, соединение с сервером было разорвано\n> Обработано: {1}/{2} || Успешно: {3}/{2} || С ошибками: {4}\n".format(x, idx2 + 1, comCount, (idx2 + 1) - len(arrСomError), len(arrСomError)))
                    if not (a in arrSomethingError):
                        arrSomethingError.append(a)
                    # Обновление общей шкалы
                    self.progressbarControl("set", self.root.progressbar2, [idx + 1, plCount])
                    self.checkLabelControl("set3", self.root.label_check2, [plCount, idx + 1, (idx + 1) - len(arrSomethingError) - len(arrConnectError), len(arrConnectError), len(arrSomethingError), "Выполнение команд"])
                    self.root.update()
                    continue

                if self.isRouters:
                    linesAns                    = chan.recv(99999).decode("utf-8").splitlines()
                    self.katprint("> Команда '{0} успешно отправлена на роутер".format(x))
                    if len(linesAns) > 0:
                        self.katprint("> Роутер дал ответ:\n>>>")
                        for line in linesAns:
                            self.katprint(">>> {}".format(line))
                        self.katprint("<<<")
                    else:
                        self.katprint("> Роутер не вернул ответа")
                else:
                    linesAns                    = stdout.read().decode("utf-8").splitlines()
                    linesErr                    = stderr.read().decode("utf-8").splitlines()
                    if len(linesErr) == 0:
                        self.katprint("> Команда '{0}' успешно выполнена".format(x))
                    else:
                        self.katprint("> [ERROR] Сервер вернул ошибку при выполнении команды '{0}'".format(x))
                    if len(linesAns) > 0:
                        self.katprint("> Ответ сервера:\n>>>")
                        for line in linesAns:
                            self.katprint(">>> {}".format(line))
                        self.katprint("<<<")
                    if len(linesErr) > 0:
                        self.katprint("> [ERROR] Сервер вернул ошибку:\n!>>>!")
                        for line in linesErr:
                            self.katprint("!>>>! {}".format(line))
                        self.katprint("!<<<!")
                        arrСomError.append(x)
                        if not (a in arrSomethingError):
                            arrSomethingError.append(a)
                self.katprint("> Обработано: {0}/{1} || Успешно: {2}/{1} || С ошибками: {3}\n".format(idx2 + 1, comCount, (idx2 + 1) - len(arrСomError), len(arrСomError)))
                # Обновление шкалы команд
                self.checkLabelControl("set4", self.root.label_check, [idx2 + 1, comCount, element[3]])
                self.progressbarControl("set", self.root.progressbar, [idx2 + 1, comCount])
                self.root.update()

            if self.isRouters:
                self.katprint ("\n> Выполнение команд на роутере '{0}' с IP-адресом {1} завершена. Успешно выполнено команд: {2} из {3}. Ошибок при выполнении: {4}\n".format(element[3], element[0], comCount - len(arrСomError), comCount, len(arrСomError)))
            else:
                self.katprint ("\n> Выполнение команд на '{0}' с IP-адресом {1} завершена. Успешно выполнено команд: {2} из {3}. Ошибок при выполнении: {4}\n".format(element[3], element[0], comCount - len(arrСomError), comCount, len(arrСomError)))
            if len(arrСomError) > 0:
                self.katprint("> Некоторые команды не удалось успешно выполнить от имени пользователя '{0}':".format(element[1]))
                for idx2, x in enumerate(arrСomError):
                    self.katprint(" {0}) '{1}'".format(idx2 + 1, x))
                self.katprint('\n')
            try:
                ssh.close()
            except:
                pass
            self.katprint("> [CONNECT] Соединение с '{0}' | {1} нормально закрыто\n\n".format(element[3], element[0]))
            
            #Обновление общей шкалы
            self.progressbarControl("set", self.root.progressbar2, [idx + 1, plCount])
            self.checkLabelControl("set3", self.root.label_check2, [plCount, idx + 1, (idx + 1) - len(arrSomethingError) - len(arrConnectError), len(arrConnectError), len(arrSomethingError), "Выполнение команд"])
            self.root.update()

        self.katprint("<===================> ВЫПОЛНЕНИЕ КОМАНД ЗАВЕРШЕНО <===================>\n> Всего обработано машин: {0}\n> Успешно завершено: {1}\n> Нет связи: {2}\n> Есть связь, но возникли какие-либо ошибки: {3}".format(plCount, plCount - len(arrSomethingError) - len(arrConnectError), len(arrConnectError), len(arrSomethingError)))
        
        if len(arrConnectError) > 0:
            self.katprint("\n===> При обработке {0} машин возникла проблема с установкой связи. Стоит проверить лог-файл '{1}', а также убедиться в доступности целей. Список проблемных элементов:".format(len(arrConnectError), self.logfileName))
            for idx, a in enumerate(arrConnectError):
                self.katprint(" {0}) '{1}' с IP-адресом {2}".format(idx + 1, self.players[a][3], self.players[a][0]))

        if len(arrSomethingError) > 0:
            self.katprint("\n===> При обработке {0} машин возникли некоторые ошибки. Стоит проверить лог-файл '{1}'. Список проблемных элементов:".format(len(arrSomethingError), self.logfileName))
            for idx, a in enumerate(arrSomethingError):
                self.katprint(" {0}) '{1}' с IP-адресом {2}".format(idx + 1, self.players[a][3], self.players[a][0]))
        self.katprint("\n\n")

        # Возвращение GUI в нормальное состояние
        self.root.protocol('WM_DELETE_WINDOW', lambda: self.confirmExit_window(None))
        self.progressbarControl("disable", self.root.progressbar, None)
        self.progressbarControl("disable", self.root.progressbar2, None)
        self.checkLabelControl("none1", self.root.label_check, None)
        self.checkLabelControl("none2", self.root.label_check2, None)
        self.buttonsActivate("enable")
        self.root.update()






# =========================================================================================================================================================================================================
# =========================================================================================================================================================================================================
# =========================================================================================================================================================================================================



    # Главное меню программы
    def mainMenu_window(self):

        root = Tk()
        self.root = root
        root.protocol('WM_DELETE_WINDOW', lambda: self.confirmExit_window(None))
        root.resizable(width=False, height=False)
        root.title("Главное меню")
        root.geometry("+20+20")
        root_frame                      = Frame(root, highlightcolor="blue", highlightbackground="blue", highlightthickness=2)
        # Отступы (чертов пайтон, хочу писать на си -_-)
        Label                           (root_frame, text=" ", width=1).grid(row=1, column=0)
        Label                           (root_frame, text=" ", width=1).grid(row=1, column=4)

        root_frame.grid                 (padx=10, pady=10)

        #/////////// Заглавные кнопки
        head_frame                      = Frame(root_frame)

        self.head_settingsButton        = Button(head_frame, text="Настройки", command= lambda: self.settings_window(None), width=15, height=1, bd=4, font=("Verdana", 8, "bold"))

        self.head_settingsButton.grid   (column=0, padx=10, sticky="w")

        head_frame.grid                 (row=0, column=0, padx=10, pady=5, columnspan=3, sticky="we")
        #/////////// Консоль
        self.cons                       = Text(root_frame, height=15, state="disabled", bg='#000000', fg='#00FF00', highlightcolor="black", highlightbackground="black", highlightthickness=1, font=("Verdana", 9, "bold"))
        cons_scroll                     = Scrollbar(root_frame, orient='vertical', command=self.cons.yview)
        self.cons['yscrollcommand']     = cons_scroll.set

        self.cons.grid                  (row=2, column=1, sticky="we", columnspan=2)
        cons_scroll.grid                (row=2, column=3, sticky='ns')
        
        # !!!!!!!!!!!  КОМПОЗИЦИЯ СПИСКОВ ПЛЕЕРОВ !!!!!!!!!!!
        lists_frame                     = Frame(root_frame)
        #/////////// Исходный список
        listAll_frame                   = Frame(lists_frame, highlightcolor="black", highlightbackground="black", highlightthickness=1)
        Label(listAll_frame, text = "Все загруженные элементы из файла:", anchor="w", bg='#808080').grid(row=0, sticky="we")
        self.root.labelCountAll         = Label(listAll_frame, text = "Количество найденных элементов: {}".format(len(self.players)), anchor="w", bg='#00FF7F')
        self.listAll                    = Listbox(listAll_frame, selectmode=SINGLE, exportselection=False, height = 30, width = 40, highlightcolor="black", highlightbackground="black", highlightthickness=1)
        listAll_scroll                  = Scrollbar(listAll_frame, orient='vertical', command=self.listAll.yview)

        self.listAll['yscrollcommand']  = listAll_scroll.set
        self.listAll.bind("<<ListboxSelect>>", self.ListboxAllSelect)

        self.root.labelCountAll.grid(row=2, sticky="we")
        self.listAll.grid               (row=1)
        listAll_scroll.grid             (row=1, column=1, sticky='ns')
        listAll_frame.grid              (row= 0, column = 0, padx=10, pady=10)
        #\
        #/////////// Кнопки редактирования списков
        listsButtons_frame              = Frame(lists_frame)
        self.root.button_lists0         = Button(listsButtons_frame, text = '>', bg='#C0C0C0', width=4, height=2, bd=4, font=("Verdana", 10, "bold"), command = lambda: self.listsUpdate(0))
        self.root.button_lists1         = Button(listsButtons_frame, text = '<', bg='#C0C0C0', width=4, height=2, bd=4, font=("Verdana", 10, "bold"), command = lambda: self.listsUpdate(1))
        self.root.button_lists2         = Button(listsButtons_frame, text = '>>>', bg='#C0C0C0', width=4, height=2, bd=4, font=("Verdana", 10, "bold"), command = lambda: self.listsUpdate(2))
        self.root.button_lists3         = Button(listsButtons_frame, text = '<<<', bg='#C0C0C0', width=4, height=2, bd=4, font=("Verdana", 10, "bold"), command = lambda: self.listsUpdate(3))

        self.root.button_lists0.grid    (row = 0, pady=10)
        self.root.button_lists1.grid    (row = 1, pady=10)
        self.root.button_lists2.grid    (row = 2, pady=10)
        self.root.button_lists3.grid    (row = 3, pady=10)

        listsButtons_frame.grid         (row= 0, column = 1, padx=0, pady=10)
        #\
        #/////////// Список активного выбора
        listActive_frame                = Frame(lists_frame, highlightcolor="black", highlightbackground="black", highlightthickness=1)
        Label(listActive_frame, text    = "Выбранные элементы:", anchor="w", bg='#808080').grid(row=0, sticky="we")
        self.root.labelCountActive      = Label(listActive_frame, text = "Количество выбранных элементов: {}".format(len(self.selected_players)), anchor="w", bg='#00FF7F')
        self.listActive                 = Listbox(listActive_frame, selectmode=SINGLE, exportselection=False, height = 30, width = 40, highlightcolor="black", highlightbackground="black", highlightthickness=1)
        listActive_scroll               = Scrollbar(listActive_frame, orient='vertical', command=self.listActive.yview)

        self.listActive['yscrollcommand'] = listActive_scroll.set
        self.listActive.bind("<<ListboxSelect>>", self.ListboxActiveSelect)

        self.root.labelCountActive.grid (row=2, sticky="we")
        self.listActive.grid            (row=1)
        listActive_scroll.grid          (row=1, column=1, sticky='ns')
        listActive_frame.grid           (row= 0, column = 2, padx=10, pady=10)
        #\
        lists_frame.grid                (row = 3, column = 1, pady=10, sticky="w")
        # \  КОМПОЗИЦИЯ СПИСКОВ ПЛЕЕРОВ \    

        # !!!!!!!!!!!  КОМПОЗИЦИЯ ДЕЙСТВИЙ !!!!!!!!!!!  
        actions_frame                   = Frame(root_frame, highlightcolor="#FF0000", highlightbackground="#FF0000", highlightthickness=1)
        #/////////// Проверка доступности плееров
        check_frame                     = Frame(actions_frame)
        self.root.button_checkPing      = Button(check_frame, text = "Проверка выбранных машин по SSH (без паролей, быстро)", bg='#C0C0C0', width = 55, height = 2, font=("Verdana", 8, "bold"), command = lambda: self.twoButtons_window("Подтверждение начала проверки по SSH (быстро)", "Инициализирвоана проверка доступности машин по SSH (без примененния логинов и паролей, быстро)\nБудет проверено единиц: {0}\nИспользуемый порт для подключения: {1}\n\nВ зависимости от их количества и интернет-соединения проверка может занять некоторое время!\nУверены, что хотите продолжить?".format(len(self.selected_players), self.sshport), "Нет", "Да", 1, 2, 0))
        self.root.button_checkSSH       = Button(check_frame, text = "Проверка выбранных машин по SSH (с паролями, медленно)", bg='#C0C0C0', height = 2, width = 55, font=("Verdana", 8, "bold"), command = lambda: self.twoButtons_window("Подтверждение начала проверки по SSH (медленно)", "Инициализирвоана проверка доступности машин по SSH (с использованием логинов и паролей, медленно)\nБудет проверено единиц: {0}\nИспользуемый порт для подключения: {1}\n\nВ зависимости от их количества и интернет-соединения проверка может занять некоторое время!\nУверены, что хотите продолжить?".format(len(self.selected_players), self.sshport), "Нет", "Да", 1, 2, 1))
        self.root.label_check           = Label(check_frame, text = "Проверка доступности машин не запущена...", highlightcolor="black", highlightbackground="black", highlightthickness=1, height = 2, font=("Verdana", 8, "bold"))
        self.root.progressbar           = Scale(check_frame, orient="horizontal", sliderlength=0, showvalue=0, state=DISABLED, takefocus=0, relief="ridge", highlightcolor="#000000", highlightbackground="#000000", highlightthickness=1, bg="#DCDCDC", troughcolor="#DCDCDC")
        #/////////// Действия с плеерами
        actions_buttons_frame           = Frame(actions_frame, highlightcolor="#000000", highlightbackground="#000000", highlightthickness=1)
        self.root.button_actionF        = Button(actions_buttons_frame, text = "ПЕРЕДАЧА ФАЙЛОВ",  width = 20, bg='#C0C0C0', font=("Verdana", 20, "bold"), command = lambda: self.plAct_window(0))
        self.root.button_actionC        = Button(actions_buttons_frame, text = "ВЫПОЛНЕНИЕ КОМАНД",  width = 20, bg='#C0C0C0', font=("Verdana", 20, "bold"), command = lambda: self.plAct_window(1))

        check_frame.grid                (row = 0)
        self.root.button_checkPing.grid (row = 0, column = 0, padx=5, pady=10, sticky="w")
        self.root.button_checkSSH.grid  (row = 0, column = 1, padx=5, pady=10, sticky="w")
        self.root.label_check.grid      (row = 1, column = 0, padx=5, pady=10, columnspan=2)
        self.root.progressbar.grid      (row = 2, column = 0, padx=5, sticky="we", columnspan=2)

        actions_buttons_frame.grid      (row = 1, padx=5, pady=100)
        self.root.button_actionF.grid   (row = 0, column = 0, padx=5, pady=10, sticky="e")
        self.root.button_actionC.grid   (row = 0, column = 1, padx=5, pady=10, sticky="w")
        #\
        #/////////// Нижний прогрессбар
        Label                       (actions_frame, text="Шкала общего прогресса с аппаратми:").grid(row=2, column=0, padx=5, pady=1, sticky="w")
        self.root.label_check2          = Label(actions_frame, text = "Операция не запущена...", highlightcolor="black", highlightbackground="black", highlightthickness=1, height = 2, font=("Verdana", 8, "bold"))
        self.root.progressbar2          = Scale(actions_frame, orient="horizontal", sliderlength=0, showvalue=0, state=DISABLED, takefocus=0, relief="ridge", highlightcolor="#000000", highlightbackground="#000000", highlightthickness=1, bg="#DCDCDC", troughcolor="#DCDCDC")
        
        self.root.label_check2.grid     (row = 3, column = 0, padx=5, pady=1, columnspan=2)
        self.root.progressbar2.grid     (row = 4, column = 0, padx=5, sticky="we", columnspan=2)
        #\
        actions_frame.grid              (row = 3, column = 2, padx=10, pady=20, sticky="ns")
        # \  КОМПОЗИЦИЯ ДЕЙСТВИЙ \  










        # Логфайл
        try:
            self.logfileName = datetime.strftime(datetime.now(), "logs\%Y.%m.%d")
            os.makedirs(self.logfileName, exist_ok=True)
            self.logfileName = "{0}\{1}_massControlTool.log".format(self.logfileName, datetime.strftime(datetime.now(), "%Y.%m.%d_%H-%M-%S"))
            self.logfile = open(self.logfileName,"w")
            self.logging = True
            self.katprint("Autor: akulov.a\n\n")
            self.katprint ("> Файл журнала '{}' успешно открыт для записи\n\n".format(self.logfileName))
        except:
            self.logging = False
            try:
                self.logfile.close()
            except:
                pass
            self.katprint("> Ошибка создания файла журнала!\n\n")
            self.twoButtons_window("Ошибка открытия '{}'".format(self.logfileName), "Файл журнала '{}' не удалось открыть или создать\nПроверьте права доступа к корневой папке программы\n\nПРОДОЛЖИТЬ ВЫПОЛНЕНИЕ ПРОГРАММЫ БЕЗ ВЕДЕНИЯ ЖУРНАЛА?".format(self.logfileName), "Нет", "Да", 0, 1, None)

        self.katprint("===> Попытка открытия файла конфигурации '{}'".format(self.settingsFileName))
            

        try:
            settingsfile = open(self.settingsFileName, 'r')
            self.katprint("> Файл конфигурации успешно открыт, выполняется чтение данных...")
            with settingsfile as file:
                for lineF in file:
                    line = lineF.rstrip('\n').split('=')
                    lineF= lineF.rstrip()
                    if line [0] != "comment":
                        if len(line) != 2:
                            self.info_window("Ошибка чтения строки: \"{}\"\n> Будут загружены параметры по умолчанию...".format(lineF), None)
                            self.setDEFAULT()
                            break

                        if line[0] == "SSHport":
                            try:
                                self.sshport = int(line[1])
                            except:
                                self.info_window("Ошибка чтения строки: \"{}\"\n> Будут загружены параметры по умолчанию...".format(lineF), None)
                                self.setDEFAULT()
                                break
                            if self.sshport < 0:
                                self.info_window("Ошибка чтения строки: \"{}\"\n> Будут загружены параметры по умолчанию...".format(lineF), None)
                                self.setDEFAULT()
                                break
                        
                        elif line[0] == "listParams":
                            arr = line[1]
                            try:
                                arr = literal_eval(arr)
                            except:
                                self.info_window("Ошибка чтения строки: \"{}\"\n> Будут загружены параметры по умолчанию...".format(lineF), None)
                                self.setDEFAULT()
                                break

                            if len(arr) != len (self.DEFAULT_listParams):
                                self.info_window("Ошибка чтения строки: \"{0}\"\nКоличество заданых параметров не совпадает с шаблонным\n> Будут загружены параметры по умолчанию...".format(lineF), None)
                                self.setDEFAULT()
                                break
                            
                            normal = True
                            for idx, x in enumerate(arr):
                                if type(x) != type(self.DEFAULT_listParams[idx]):
                                    normal = False
                            if not normal:
                                self.info_window("Ошибка чтения строки: \"{}\"\nТипы заданых параметров не совпадют с шаблонными\n> Будут загружены параметры по умолчанию...".format(lineF), None)
                                self.setDEFAULT()
                                break
                            else:
                                self.listParams = arr

            self.katprint("> Параметры успешно загружены из файла конфигурации\n")                        
        except:
            self.katprint("> Не удалось открыть файл конфигурации - возможно, сохраненная конфигурация отсутствует (скорее всего), либо нет прав на чтение файла '{}'\n> Используются настройки по умолчанию...\n".format(self.settingsFileName))
        try:
            settingsfile.close()
        except:
            pass

        if self.listParams[0] == 0:
            self.katprint("===> Инициализирована пересборка списка машин из файла - поиск файла со списком машин...")
            try:
                filePlayers = open(self.listParams[1], 'r')
            except:
                self.info_window("Ошибка открытия файла списка машин\nПроверьте наличие файла '{}', а также его доступность\nВозможно, у пользователя нет прав на чтение файла".format(self.listParams[1]), None)
                try:
                    filePlayers.close()
                except:
                    pass
                self.listSettings_window(None)
                return

            temp_array      = []
            self.katprint("> Файл '{}' успешно открыт\n\n===> Попытка чтения списка машин...".format(self.listParams[1]))
            with filePlayers as file:
                for line in file:
                    if not ((line == '') or line.isspace()):
                        line = line.rstrip('\n').split(':')
                        if line [0] != "comment":
                            if len(line) < 4:
                                self.info_window("Ошибка чтения строки \" {0} \" файла '{1}'\n\n{2}".format(line, self.listParams[1], self.infoText1), None)
                                self.listSettings_window(None)
                                return
                            temp_array.append([line[0], line[1], line[2], line[3]]) # 0 - IP адрес, 1 - имя пользователя, 2 - пароль, 3 - имя плеера
            try:
                filePlayers.close()
            except:
                pass

            if len(temp_array) == 0:
                self.info_window("В файле '{0}' не найдено необходимых записей.\n{1}".format(self.listParams[1], self.infoText1 + self.infoText2), None)
                self.listSettings_window(None)
                return
            else:
                self.katprint( "> В файле '{0}' найдено данных: {1}\n".format(self.listParams[1], len(self.players)) )

            self.players    = temp_array
            self.listsRebuild()

        root.mainloop()

        





# |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

if __name__ == '__main__':
    main = massControlTool()
    main.mainMenu_window()