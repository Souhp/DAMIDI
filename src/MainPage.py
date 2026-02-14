import flet as ft
from Event_Dispatch_Bus import trigger_event
from PageMemory import remember_page
from DefaultStructures import  Default_Page,SearchField
import asyncio


class MainPage(Default_Page):
    
    ###I SPENT SO MUCH TIME JUST TO LEARN THAT
    # IF YOU CALL A FUNCTION THATS IMPORTED  DIRECTLY IN THE FLET BUTTON 
    # IT JUST RUNS IT ON STARTUP AND THEN NEVER TRIGGERS AGAIN
    #THIS IS FLUFF, theres a good reason for this im sure but aaaa

    async def Settings_Click(self, e):

        remember_page(self)
        await trigger_event("change_to_settings")



    async def change_page_soft_click(self,e: ft.ControlEvent):

        print(f'{e}')
        softref = str(e.control.text)
        remember_page(self)
        print("SSSSS")

        await trigger_event("change_page_soft",softref)









                                    ##SETUP###

    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.name = "MAINPAGE"
                    ##HEADER##



        self.Settings_Btn= ft.FloatingActionButton(

    
        icon=ft.Icons.SETTINGS,
    
        on_click = self.Settings_Click
        )

        self.Search_Field = SearchField(ft.MainAxisAlignment.CENTER)

    
        self.Header=ft.Row(

            controls=[self.Settings_Btn,self.Search_Field.Row],
            alignment=ft.alignment.top_left
    
            )


                    ##BODY##



        Game_Grid = ft.GridView(

            #expand=1,
            runs_count=5,
            #max_extent=150,
            child_aspect_ratio=1,
            #spacing=5,
            #run_spacing=5, 
            expand=False


            )

        ##THIS WILL BE REFACTORED TO HAVE CUSTOM GAMES AND MAKE IT EASIER TO ADD GAMES
        premadeGameList = {

            "Chord_Id_App":"game_icons/chord_id.png",
            "Piano_Rush":"game_icons/piano_rush.png",
            "Testing_App":"game_icons/chord_id.png",
			"guessChord":"game_icons/chord_id.png",


        }
        loop = asyncio.get_event_loop()

        for i,k in premadeGameList.items():


            Game_Grid.controls.append(

                ft.ElevatedButton(

                    text=i,
                    on_click = self.change_page_soft_click,
                    expand=False,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    content=ft.Column(controls=[ft.Image(src=k),ft.Text(i),]),
                    

                

                
                
    
                )

                )









                ##ALL TOGETHER###




        ###(Music_Page)THIS IS A VARIABLE THATS INHERITED AND CAN BE ACCESSED
        #THROUGH THE CHANGE PAGE FUNCTION TO THAT I DONT HAVE TO MAKE AN INDIVIDUAL FUNCTION FOR EACH PAGE CHANGE 
        ##AND BE ABLE TO REMEMBER THE PAST PAGE WHEN GOING BACK

    

        self.content = ft.Container(


            ft.Column(

    
                controls=[self.Header,Game_Grid],
                #alignment=ft.MainAxisAlignment.START,
                expand=True
                ),
            expand=True,

            
    
    
            )




