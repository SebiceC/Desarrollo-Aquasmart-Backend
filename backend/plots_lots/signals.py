from django.db import transaction
from .models import SoilType,CropType
def create_default_soilt_types(sender, **kwargs):  
   
    try:
        default_types = {
            1: "Arcilla",
            2: "Franco arcilloso",
            3: "Franco",
            4: "Franco arenoso",
            5: "Arena",
            6: "Arcilla arenosa",
            7: "Franco arcilloarenoso",
            8: "Limo",
            9: "Arcilla limosa",
            10: "Franco arcillolimoso",
            11: "Franco limoso",           
        }

        with transaction.atomic():
            for id, name in default_types.items():
                SoilType.objects.update_or_create(
                    id=id,
                    defaults={"name": name}
                )

    except Exception as e:
        print(f"Error creando tipos de suelo: {e}")
        
def create_default_crop_types(sender, **kwargs): 
         
    try:
        default_types = {
            1:"Piscicultura",
            2:"Agricultura" ,      
        }

        with transaction.atomic():
            for id, name in default_types.items():
                CropType.objects.update_or_create(
                    id=id,
                    defaults={"name": name}
                )

    except Exception as e:
        print(f"Error creando tipos de cultivo: {e}")        