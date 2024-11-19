#!/bin/bash

# Ruta al proyecto y entorno virtual
PROJECT_PATH="/home/fse08/proyecto"
VENV_PATH="$PROJECT_PATH/venv"
PROGRAM_PATH="$PROJECT_PATH/pro1.py"

# Crear el script de inicio
cat << EOF > $PROJECT_PATH/startup_script.sh
#!/bin/bash

# Activar entorno virtual
source $VENV_PATH/bin/activate

# Ejecutar el programa
cd $PROJECT_PATH
python pro1.py
EOF

# Dar permisos de ejecución
chmod +x $PROJECT_PATH/startup_script.sh

# Crear el servicio systemd
cat << EOF > /etc/systemd/system/proyecto.service
[Unit]
Description=Proyecto de Sensores
After=network.target

[Service]
Type=simple
User=fse08
WorkingDirectory=$PROJECT_PATH
ExecStart=$PROJECT_PATH/startup_script.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd y habilitar el servicio
systemctl daemon-reload
systemctl enable proyecto.service
systemctl start proyecto.service
