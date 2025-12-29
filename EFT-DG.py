from pydglab_ws import DGLabWSServer,DGLabWSConnect,StrengthData, FeedbackButton, Channel, StrengthOperationType, RetCode
import qrcode
import asyncio
import pyautogui
import numpy as np
import time
import configparser as ConfigParser
config = ConfigParser.ConfigParser()
power=0
Set2K=[int(2560*0.014),int(1440*0.02),int(2560*0.048),int(1440*0.2)]
####Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting####
with open('readme.txt', 'w') as rdm: 
     rdm.write("#####################################\n")
     rdm.write("本项目目前只支持2560x1440分辨率显示器\n")
     rdm.write("开启N卡或其他游戏滤镜可能导致识别不准 请到config.ini中手动修改识别参数\n")
     rdm.write("使用DG-LAB3.0APP WSsocket连接\n")
     rdm.write("需在塔科夫游戏内设置 健康状态持续显示 为彩色\n")
     rdm.write("郊狼连接A通道 \n")
     rdm.write("上面一排按钮 开启波形输出 下面一排按钮关闭波形输出\n")
     rdm.write("#####################################\n")
     rdm.write("设置解释：\n")
     rdm.write("LocalIP:本机在局域网内的ip\n")
     rdm.write("Ratelimit:识别计算频率限制(S)\n")
     rdm.write("HPlow/high:low为强度最大时的血量值,high为开始通电时的血量值\n")
     rdm.write("LocalIP:本机在局域网内的ip\n")
     rdm.write("LocalIP:本机在局域网内的ip\n")
     rdm.write("powerlimit 强度上限(需将手机端的 '最低强度上限' 设置为与该值相同 或设置为200-200)\n")
     rdm.write("BagColorMin/Max: 背包采样点颜色范围\n")
     rdm.write("RoleHmax: 彩色小人识别色相最大值\n")
     rdm.write("RoleSmin/max: 彩色小人识别饱和度范围\n")
     rdm.write("roleVmin/max:彩色小人识别灰度范围\n")
     rdm.write("temprate:强度变化缓冲率\n")
     rdm.write("#####################################\n")
     rdm.write("Bilibili: 是扒一扒喵\n")
     rdm.write("QQ:2889613770\n")
     rdm.write("#####################################\n")

ScreenSet=Set2K
def first(config):
    global LocalIP
    global PowerLimit
    global Ratelimit
    global BagColorMax
    global BagColorMin
    global RoleHmax
    global RoleHmin
    global RoleSmin
    global RoleVMax
    global RoleVMin
    global tempRate
    global HPhigh
    global HPlow
    global Wave
    LocalIP=config.get(section="Basic",option="LocalIP")
    PowerLimit=config.getfloat(section="Basic",option="PowerLimit")
    Ratelimit =config.getfloat(section="Basic",option="Ratelimit")
    BagColorMin=eval(config.get(section="Advanced",option="BagColorMin") )
    BagColorMax=eval(config.get(section="Advanced",option="BagColorMax"))
    RoleHmax=config.getfloat(section="Advanced",option="RoleHmax")
    RoleHmin=config.getfloat(section="Advanced",option="RoleHmin")
    RoleSmin=config.getfloat(section="Advanced",option="RoleSmin")
    RoleVMax=config.getfloat(section="Advanced",option="RoleVMax")
    RoleVMin=config.getfloat(section="Advanced",option="RoleVMin")
    tempRate=config.getfloat(section="Advanced",option="tempRate")
    HPlow =config.getfloat(section="Basic",option="HPlow")
    HPhigh =config.getfloat(section="Basic",option="HPhigh")
    Wave = eval(config.get(section="Wave",option="wave"))
    
     

config.read('config.ini')

if(config.sections()==[]):
    config['Basic'] = { 'LocalIP': '192.168.101.66', 'PowerLimit': 60, 'Ratelimit': 0.2 ,'HPlow':100, 'HPhigh':435} 
    config['Advanced'] = { 'BagColorMin': [39,49,66] , 'BagColorMax': [43,53,70] ,"RoleHmax":130,'RoleHmin':0,'RoleSmin':0.4,'RoleVMax':0.6,'RoleVMin':0.2,'tempRate':0.3 } 
    config['Wave'] ={'wave': [
        ((11, 11, 11, 11), (100, 100, 100, 100)), ((11, 11, 11, 11), (20, 20, 20, 20)),((11, 11, 11, 11), (100, 100, 100, 100)),((11, 11, 11, 11), (100, 100, 100, 100)), ((11, 11, 11, 11), (40, 40,40, 40)), ((11, 11, 11, 11), (95, 95,95, 95)), ((11, 11, 11, 11), (100, 100,100, 100)), ((20, 20, 20, 20), (50, 50,50, 50)),
        ((20, 20, 20, 20), (0, 0, 0, 0)), ((20, 20, 20, 20), (50, 50, 50, 50)),((20, 20, 20, 20), (100, 100, 100, 100)), ((20, 20, 20, 20), (100, 100,100, 100)), ((20, 20, 20, 20), (50, 50,50, 50)), ((20, 20, 20, 20), (0, 0,0, 0)), ((20, 20, 20, 20), (50, 50,50, 50)),((20, 20, 20, 20), (100, 100,100, 100)),
        ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)),((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)),
       ((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100)),((25, 25, 25, 25), (100, 100, 100, 100)), ((25, 25, 25, 25), (100, 100, 100, 100))
       ]}
    with open('config.ini', 'w') as configfile: 
        config.write(configfile)
    print("Created Default Config File")
    first(config)
else:
    config.read('config.ini')
    first(config)
for a in range(0,10):
    print("Read the README.TXT at first pls")
print("LocalIP=",LocalIP)



####Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting####
n_ar=np.array([0,0,0])
arrrr=np.array([])
pointsnum=ScreenSet[2]*ScreenSet[3]
msk=[2030,11527,11951,16595,17017,23127,24322]
Dlist=[int((msk[0]/35136)*pointsnum),int((msk[1]/35136)*pointsnum),int((msk[2]/35136)*pointsnum),int((msk[3]/35136)*pointsnum),int((msk[4]/35136)*pointsnum),int((msk[5]/35136)*pointsnum),int((msk[6]/35136)*pointsnum)]
Li=np.delete(np.array(range(0,35136)),Dlist)
PULSE_DATA = {'wave':Wave}
def rgb2hsv(r, g, b):
    r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    m = mx-mn
    if mx == mn:
        h = 0
    elif mx == r:
        if g >= b:
            h = ((g-b)/m)*60
        else:
            h = ((g-b)/m)*60 + 360
    elif mx == g:
        h = ((b-r)/m)*60 + 120
    elif mx == b:
        h = ((r-g)/m)*60 + 240
    if mx == 0:
        s = 0
    else:
        s = m/mx
    v = mx
    return h, s, v
temp=440
def print_qrcode(_: str):
    url = _
    qr = qrcode.QRCode(
    version=1, # 控制二维码大小，1 为最小
    error_correction=qrcode.constants.ERROR_CORRECT_L, # 纠错水平
    box_size=5, # 每个方块的像素大小
    border=1, # 边框宽度
    )
    qr.add_data(url)
    qr.make(fit=True)
    im = qr.make_image(fill_color="black", back_color="white")
    im = im.convert("L")
    im.show()
gamestate="other"
gamestate2="other"

client = None
   
async def send():
    try:####Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting####
        try:
            global client
            global Ratelimit
            time.sleep(Ratelimit)
            global PowerLimit #强度上限 需与APP的最低上限一致
            global BagColorMin
            global BagColorMax
            global RoleHmax
            global RoleHmin
            global RoleSmin
            global tempRate
            global RoleVMin
            global RoleVMax

            lg=0
            global temp
            global gamestate
            global gamestate2
            global power
            global HPlow
            global HPhigh
            i =pyautogui.screenshot(region=ScreenSet)
            i_ar=np.array(i)
            #应用蒙版
            points= np.delete(i_ar.reshape([-1,3]),Li,axis=0)
            #取样7像素点
            Cw=[0.0795,0.1931,0.1363,0.1363,0.1591,0.1477,0.1477]
            #按血量加权
            Rgb=np.average(points,axis=0,weights=Cw)
            #平均 得到整体平均颜色

            
            hss=rgb2hsv(Rgb[0],Rgb[1],Rgb[2])
            #rgb2hsv
            x1=(hss[0]/360)*(hss[1]*hss[2])
            #将h s v关联到一起作为x代入回归方程
            if ((RoleHmin<=np.array(hss)[0]<RoleHmax)and(np.array(hss)[1]>=RoleSmin) and (RoleVMin<np.array(hss)[2]<RoleVMax)): #检测小绿人
                ps=(258597.6*(x1*x1*x1)-75978.385*(x1*x1)+9241.92*x1+0.05899)+7
                #将X代入经验回归求人物血量
                hp=(ps*tempRate+temp*(1-tempRate))
                temp=hp
                #缓冲
                if hp>=HPhigh:
                        lg=0
                        
                else:
                    if hp>=0:
                        lg=PowerLimit*(((440-hp)/(440-HPlow))) #计算强度
                        
                    if hp<0:
                        lg=PowerLimit
                        
                if lg>=PowerLimit:
                        lg=PowerLimit
                        
                else:
                        lg=lg
                if (gamestate =="game" and gamestate2 =="game") or(gamestate2 !="other" and gamestate !="game") or (gamestate2 !="game" and gamestate !="other")or (gamestate2 =="game" and gamestate !="game")or (gamestate2 !="game" and gamestate =="game"): 
                    print("STATE:INGAME","HP:",hp,"Power:",lg)
                    power = lg
                    await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(lg))
                else:
                    print("STATE:INGAME","HP:",hp,"Power:",power)
                    await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                    
                
                
                
                gamestate="game"
                
                

            elif(BagColorMin[0]<points[0][0]<BagColorMax[0]) and (BagColorMin[1]<points[0][1]<BagColorMax[1]) and (BagColorMin[2]<points[0][2]<BagColorMax[2]):
                gamestate="bag"    
                print("STATE:IN BAG","Power:",power)
                await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                

            else:
                if(gamestate =="game" and gamestate2 == "game"):
                     print("STATE:INGAME","HP:",hp,"Power:",power)
                     await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                else:
                    gamestate="other"
                    print("STATE:Not In Game","Power: 0")
                    await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(0))
        except all as ww:
             print(ww)

            ####Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting########Setting####
        try:
    
            
            time.sleep(Ratelimit)

            lg=0
            i =pyautogui.screenshot(region=ScreenSet)
            i_ar=np.array(i)
            #应用蒙版
            points= np.delete(i_ar.reshape([-1,3]),Li,axis=0)
            #取样7像素点
            Cw=[0.0795,0.1931,0.1363,0.1363,0.1591,0.1477,0.1477]
            #按血量加权
            Rgb=np.average(points,axis=0,weights=Cw)
            #平均 得到整体平均颜色

            
            hss=rgb2hsv(Rgb[0],Rgb[1],Rgb[2])
            #rgb2hsv
            x1=(hss[0]/360)*(hss[1]*hss[2])
            #将h s v关联到一起作为x代入回归方程
            if ((RoleHmin<=np.array(hss)[0]<RoleHmax)and(np.array(hss)[1]>=RoleSmin) and (RoleVMin<np.array(hss)[2]<RoleVMax)): #检测小绿人
                ps=(258597.6*(x1*x1*x1)-75978.385*(x1*x1)+9241.92*x1+0.05899)+7
                #将X代入经验回归求人物血量
                hp=(ps*tempRate+temp*(1-tempRate))
                temp=hp
                #缓冲
                if hp>=430:
                        lg=0
                        
                else:
                    if hp>=0:
                        lg=PowerLimit*(((440-hp)/(440-HPlow)))
                        
                    if hp<0:
                        lg=PowerLimit
                        
                if lg>=PowerLimit:
                        lg=PowerLimit
                        
                else:
                        lg=lg
                if (gamestate =="game" and gamestate2 =="game") or(gamestate !="other" and gamestate2 !="game")or (gamestate2 !="other" and gamestate !="game")or (gamestate2 =="game" and gamestate !="game")or (gamestate2 !="game" and gamestate =="game"): 
                        print("STATE:INGAME","HP:",hp,"Power:",lg)
                        power = lg
                        await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(lg))
                        
                else:
                        print("STATE:INGAME","HP:",hp,"Power:",power)
                        await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                        
                
                
                
                gamestate2="game"
                

            elif(BagColorMin[0]<points[0][0]<BagColorMax[0]) and (BagColorMin[1]<points[0][1]<BagColorMax[1]) and (BagColorMin[2]<points[0][2]<BagColorMax[2]):
                
                
                await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                gamestate2="bag"    
                print("STATE:IN BAG","Power:",power)

            else:
                if(gamestate =="game" and gamestate2 == "game"):
                     print("STATE:INGAME","HP:",hp,"Power:",power)
                     await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                else:
                    gamestate2="other"
                    print("STATE:Not In Game","Power: 0")
                    await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(0))
            
        except all as ww:
            print(ww)
            
        
        
    except all as ww:
            print(ww)

   
Enable = 0
async def main():
    
    async with DGLabWSServer("0.0.0.0", 5679, 60) as server:
        global client
        client = server.new_local_client()
        
                
            

        url = client.get_qrcode("ws://"+LocalIP+":5679")
        print("Scan the QRCODE with DG-Lab App")
        print_qrcode(url)
        # 等待绑定
        
        await client.bind()
        pulse_data_iterator = iter(PULSE_DATA.values())
        
        print(f"Binded with APP {client.target_id}")

        async for data in client.data_generator():      
            if isinstance(data, FeedbackButton):    
                

                if data == FeedbackButton.A1 or data == FeedbackButton.A2 or data == FeedbackButton.A3 or data == FeedbackButton.A4 or data == FeedbackButton.A5:
                    print("Wave Out Enabled")
                    Enable=1
                if data == FeedbackButton.B1 or data == FeedbackButton.B2 or data == FeedbackButton.B3 or data == FeedbackButton.B4 or data == FeedbackButton.B5:
                    print("Wave Out Disabled")
                    Enable=0
                    
            try:
                await send()
                pulse_data_current = next(pulse_data_iterator, None)    # 当前准备发送的波形
                # 如果波形都发送过了，则开始新一轮的发送
                if(Enable==1):
                    if not pulse_data_current:
                        pulse_data_iterator = iter(PULSE_DATA.values())
                        continue
                    await client.add_pulses(Channel.A, *(pulse_data_current))
                else:
                    await client.clear_pulses(Channel.A)


            except:
                pass    
       
        

if __name__ == "__main__":
    asyncio.run(main())
    
    
    




