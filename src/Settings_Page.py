import flet as ft

from Event_Dispatch_Bus import trigger_event
import PageMemory
import mido
from DefaultStructures import Default_Page
import asyncio


#main_loop = asyncio.get_event_loop()
class settings(Default_Page):



    def get_ports(e):
        ports = []
        print("aaa")
        for port in mido.get_input_names():
            port_inst = "{}".format(port)
            ports.append(ft.dropdown.Option(key=(port_inst)))

        return ports



    async def trigger_midi_change(self, e: ft.ControlEvent):
        await trigger_event("change_midi", e.control.value)


    ####THIS IS FUCKED, AS A CLASS FOR SOME REASON THE BUTTON PRESS ALSO REVIEVES (X) A BUNCH OF EXTRA INFO, 
    ##WOULD BE NICE TO KNOW WHY THIS IS HAPPENING TO BE ABLE TO RECREATE THIS IN THE FUTURE




    def __init__(self, *args, **kwargs):

        
        super().__init__(*args, **kwargs)

        ##HEADER####


        Back_Button = ft.FloatingActionButton(

    
            icon=ft.Icons.ARROW_BACK,
            on_click=self.click_bb
            )

        Header = ft.Row(

            controls=[Back_Button]
    
            )


        self.dropdown=ft.Dropdown(


            options=self.get_ports(),
            text_size=17,
            on_change=self.trigger_midi_change,
            )



        options = ft.Column(

            expand=True,
            alignment= ft.MainAxisAlignment.CENTER,
            controls=[


                ###SETTINGS TITLE###
                ft.Container(
                    ft.Text(
                        "SETTINGS",
                        weight=ft.FontWeight.BOLD,
                        size=30),
                        alignment=ft.alignment.center
            
                    ),
                ##SETTINGS OPTIONS/CONTENT####
                ft.Row(


                    alignment=ft.MainAxisAlignment.CENTER,        
                    controls=[

                        ft.Text("Midi Input:",size=20),
            
            
            
                        self.dropdown,


                        ft.FloatingActionButton(
                            icon=ft.Icons.REFRESH,
                            on_click=lambda e:self.dropdown.update
                            )
                     
                        ]

                    )
                ]
            )

        self.content = ft.Container(

            ft.Column(

                #alignment= ft.alignment.center,
                controls=[Header,options]
                ),

            #THISS MAKES SURE THE OUTER PART (BACK BUTTON ECT) is at top
            expand=True

            )






