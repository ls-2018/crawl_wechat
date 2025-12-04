py2applet --make-setup main.py bj.ico --iconfile bj.ico
python3 setup.py py2app -O2
python3 setup.py py2app -A # 软连接  方便本地开发
# OPTIONS = {'iconfile': 'bj.ico'}
# cp admission_letter.py /Applications/admission.app/Contents/MacOS/admission
