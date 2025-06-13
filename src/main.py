

from Event_Dispatch_Bus import register_event
import flet as ft
from MainPage import MainPage
import Settings_Page
import PageMemory
import asyncio
import DefaultStructures
import importlib
import tracemalloc
tracemalloc.start()


initialized_class= None
Midi_Name = "ForFl 2"
setting_page_inst = Settings_Page.settings()


async def main(page: ft.Page):
    
 
#UNIQUE FUNTIONS###    

    
    async def total_update(*args,**kwargs):
        page.update() 
        print("tu")
        page.update()




    async def Change_To_Settings(*args,**kwargs):
        #page.controls.remove(currentPage)
        page.controls.clear()
        page.controls.append(setting_page_inst.content)
        page.update() 
        print("BANANA")



    







    async def Change_Page(NewPage):

        if NewPage is None:
            print("ERROR: NewPage is None — cannot change page")
            return
        page.controls.clear()
        currentPage = NewPage
        page.controls.append(currentPage.content)
        page.update()    
        print("ChangePAGEaaa")
    


    async def Change_Page_Soft(softref):
        


        class_inst = getattr(importlib.import_module(softref),"App_Inst")
        global initialized_class
        initialized_class = class_inst()

        if initialized_class.All_Content is None:
            print("ERROR: NewPage is None — cannot change page")
            return
        page.controls.clear()
        currentPage = initialized_class
        page.controls.append(currentPage.All_Content)
        page.update()    
        print("ChangePAGESOFT")

        await initialized_class.async_init(midi_input=Midi_Name)




    async def Change_Midi(CurrentMidi):
        print("recieved:  ", CurrentMidi)
        global Midi_Name
        Midi_Name = CurrentMidi
        






    ##Sets the page to the main page by default
    
    currentPage = MainPage()

    #event dispatch
    await register_event("change_to_settings",Change_To_Settings)
    await register_event("change_page",Change_Page)
    await register_event("change_midi",Change_Midi)
    await register_event("change_page_soft",Change_Page_Soft)
    await register_event("total_update",total_update)

    page.controls.append(currentPage.content)
    #alignment=ft.MainAxisAlignment.CENTER,
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    page.update()



    

ft.app(main)