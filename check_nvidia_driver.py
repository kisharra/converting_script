import subprocess

def check_nvidia_driver():
    try:
        # Выполняем команду lspci для проверки наличия устройства Nvidia
        lspci_output = subprocess.check_output(["lspci"])
        # Проверяем, есть ли строка с указанием Nvidia в выводе lspci
        if b"NVIDIA" in lspci_output:
            print("Nvidia видеодрайвер обнаружен.")
        else:
            print("Нет Nvidia видеодрайвера.")
    except subprocess.CalledProcessError:
        print("Ошибка выполнения команды lspci.")

check_nvidia_driver()