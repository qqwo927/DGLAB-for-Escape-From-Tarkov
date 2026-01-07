from pydglab_ws import DGLabWSServer,DGLabWSConnect,StrengthData, FeedbackButton, Channel, StrengthOperationType, RetCode
import qrcode
import asyncio
import pyautogui
import numpy as np
import time
import socket
import psutil
import configparser as ConfigParser
config = ConfigParser.ConfigParser()
power=0
Set2K=[int(2560*0.014),int(1440*0.02),int(2560*0.048),int(1440*0.2)]
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
    global RoleSmax
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
    RoleHmax=eval(config.get(section="Advanced",option="RoleHsvmax"))[0]
    RoleHmin=eval(config.get(section="Advanced",option="RoleHsvmin"))[0]
    RoleSmax=eval(config.get(section="Advanced",option="RoleHsvmax"))[1]
    RoleSmin=eval(config.get(section="Advanced",option="RoleHsvmin"))[1]
    RoleVMax=eval(config.get(section="Advanced",option="RoleHsvMax"))[2]
    RoleVMin=eval(config.get(section="Advanced",option="RoleHsvMin"))[2]
    tempRate=config.getfloat(section="Advanced",option="tempRate")
    HPlow =config.getfloat(section="Basic",option="HPlow")
    HPhigh =config.getfloat(section="Basic",option="HPhigh")
    Wave = eval(config.get(section="Wave",option="wave"))
config.read('config.ini')

if(config.sections()==[]):
    config['Basic'] = { 'LocalIP': '111.111.111.111', 'PowerLimit': 60, 'Ratelimit': 0.4 ,'HPlow':100, 'HPhigh':435} 
    config['Advanced'] = { 'BagColorMin': [39,49,66] , 'BagColorMax': [43,53,70] ,"RoleHsvmax":[130,1,0.6],'RoleHsvmin':[0,0.4,0.1],'tempRate':0.3 } 
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
hp=440
   
async def send():
    try:
        global client
        global Ratelimit
        time.sleep(Ratelimit)
        global PowerLimit
        global BagColorMin
        global BagColorMax
        global RoleHmax
        global RoleHmin
        global RoleSmin
        global RoleSmax
        global tempRate
        global RoleVMin
        global RoleVMax
        global hp

        lg=0
        global temp
        global gamestate
        global gamestate2
        global power
        global HPlow
        global HPhigh
        try:
           
            i =pyautogui.screenshot(region=ScreenSet)
            i_ar=np.array(i)
            points= np.delete(i_ar.reshape([-1,3]),Li,axis=0)
            Cw=[0.0795,0.1931,0.1363,0.1363,0.1591,0.1477,0.1477]

            Rgb=np.average(points,axis=0,weights=Cw)

            ps=0
            hsv=[]
            for hs in points:
                hsv.append(rgb2hsv(hs[0],hs[1],hs[2]))
            hsv=np.array(hsv)
            hss=rgb2hsv(Rgb[0],Rgb[1],Rgb[2])
            
            x1=(hss[0]/360)*(hss[1]*hss[2])

            if ((RoleHmin<=np.array(hss)[0]<RoleHmax)and(RoleSmax>np.array(hss)[1]>=RoleSmin) and (RoleVMin<=np.array(hss)[2]<RoleVMax)): 
                ps=(258597.6*(x1*x1*x1)-75978.385*(x1*x1)+9241.92*x1+0.05899)+7
                hp=(ps*tempRate+temp*(1-tempRate))
                temp=hp
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
                    power = lg
                    dbg="\n\n"+str(hsv)+"|"+str(np.array(hss))+"|"+str(ps)+"|"+str(power)
                    
                    print(dbg+"|  STATE:INGAME","HP:",hp,"Power:",lg)
                    await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(lg))
                else:
                    dbg=str(hsv)+"|"+str(np.array(hss))+"|"+str(ps)+"|"+str(power)
                    print(dbg+"|  STATE:INGAME","HP:",hp,"Power:",power)
                    await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                    
                
                
                
                gamestate="game"
                
                

            elif(BagColorMin[0]<points[0][0]<BagColorMax[0]) and (BagColorMin[1]<points[0][1]<BagColorMax[1]) and (BagColorMin[2]<points[0][2]<BagColorMax[2]):
                gamestate="bag"    
                dbg="\n\n"+str(hsv)+"|"+str(np.array(hss))+"|"+str(ps)+"|"+str(power)
                print(dbg+"|  STATE:IN BAG","Power:",power)
                await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                

            else:
                if(gamestate =="game" and gamestate2 == "game"):
                     dbg="\n\n"+str(hsv)+"|"+str(np.array(hss))+"|"+str(ps)+"|"+str(power)
                     print(dbg+"|  STATE:INGAME","HP:",hp,"Power:",power)
                     await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                     gamestate="other"
                else:
                    gamestate="other"
                    dbg="\n\n"+str(hsv)+"|"+str(np.array(hss))+"|"+str(ps)+"|"+str(power)
                    print(dbg+"|  STATE:Not In Game","Power: 0")
                    await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(0))
        except all as ww:
             print(ww)
        try:
    
            
            time.sleep(Ratelimit)

            lg=0
            i =pyautogui.screenshot(region=ScreenSet)
            i_ar=np.array(i)
  
            points= np.delete(i_ar.reshape([-1,3]),Li,axis=0)
  
            Cw=[0.0795,0.1931,0.1363,0.1363,0.1591,0.1477,0.1477]

            Rgb=np.average(points,axis=0,weights=Cw)
            ps=0
            hsv=[]
            for hs in points:
                hsv.append(rgb2hsv(hs[0],hs[1],hs[2]))
            hsv=np.array(hsv)
            hss=rgb2hsv(Rgb[0],Rgb[1],Rgb[2])


            x1=(hss[0]/360)*(hss[1]*hss[2])
            if ((RoleHmin<=np.array(hss)[0]<RoleHmax)and(RoleSmax>np.array(hss)[1]>=RoleSmin) and (RoleVMin<=np.array(hss)[2]<RoleVMax)): 
                ps=(258597.6*(x1*x1*x1)-75978.385*(x1*x1)+9241.92*x1+0.05899)+7
            
                hp=(ps*tempRate+temp*(1-tempRate))
                temp=hp
          
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
                        
                        power = lg
                        dbg="\n\n"+str(hsv)+"|"+str(np.array(hss))+"|"+str(ps)+"|"+str(power)
                        print(dbg+"|  STATE:INGAME","HP:",hp,"Power:",lg)
                        await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(lg))
                        
                else:
                        dbg="\n\n"+str(hsv)+"|"+str(np.array(hss))+"|"+str(ps)+"|"+str(power)
                        print(dbg+"|  STATE:INGAME","HP:",hp,"Power:",power)
                        await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                        
                
                
                
                gamestate2="game"
                

            elif(BagColorMin[0]<points[0][0]<BagColorMax[0]) and (BagColorMin[1]<points[0][1]<BagColorMax[1]) and (BagColorMin[2]<points[0][2]<BagColorMax[2]):
                
                
                await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                gamestate2="bag" 
                dbg="\n\n"+str(hsv)+"|"+str(np.array(hss))+"|"+str(ps)+"|"+str(power)   
                print(dbg+"|  STATE:IN BAG","Power:",power)

            else:
                if(gamestate =="game" and gamestate2 == "game"):
                     dbg="\n\n"+str(hsv)+"|"+str(np.array(hss))+"|"+str(ps)+"|"+str(power)
                     print(dbg+"|  STATE:INGAME","HP:",hp,"Power:",power)
                     await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(power))
                     gamestate2="other"
                else:
                    gamestate2="other"
                    dbg="\n\n"+str(hsv)+"|"+str(np.array(hss))+"|"+str(ps)+"|"+str(power)
                    print(dbg+"|  STATE:Not In Game","Power: 0")
                    await client.set_strength(Channel.A,StrengthOperationType.SET_TO,int(0))
            
        except all as ww:
            print(ww)
            
        
        
    except all as ww:
            print(ww)

   
Enable = 0
async def main():
    global LocalIP
    if(LocalIP=="111.111.111.111"):
        print("==========================")
        # 获取Windows网卡地址及IPV4地址列表
        addrs = psutil.net_if_addrs()
        candidates = []
        for iface_name, iface_addrs in addrs.items():
            for addr in iface_addrs:
                if addr.family == socket.AF_INET:
                    ip_str = addr.address
                    # 排除掉本地环回地址
                    if ip_str.startswith("127.") or ip_str.startswith("169.254"):
                        continue
                    candidates.append((iface_name, ip_str))
        if not candidates:
            print("未找到有效的局域网IP地址。请手动到config文件里修改本机IP(LOCALIP)及强度上限(POWERLIMIT)")
            input("按回车键关闭程序")
        else:
            print("检测到以下网卡地址及IP：")
            for idx, (iface, ip) in enumerate(candidates):
                print(f"{idx+1}. {iface}: {ip}")
            print("==========================")
            while LocalIP == "111.111.111.111":
                selection = input("请输入对应网卡前的数字进行选择, 或输入q退出: ")
                if selection.lower() == 'q':
                    exit(0)
                if selection.isdigit() and 1 <= int(selection) <= len(candidates):
                    chosen_ip = candidates[int(selection)-1][1]
                    LocalIP = chosen_ip
                    print(f"已经临时修改LOCALIP为: {chosen_ip}")
                else:
                    print("无效输入，请重新输入对应的数字。")
            
    async with DGLabWSServer("0.0.0.0", 5678, 60) as server:
        global client
        global Enable
        client = server.new_local_client()
        
        url = client.get_qrcode("ws://"+LocalIP+":5678")
        print("Scan the QRCODE with DG-Lab App")
        print_qrcode(url)

        
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
                pulse_data_current = next(pulse_data_iterator, None)   
        
                if(Enable==1):
                    if not pulse_data_current:
                        pulse_data_iterator = iter(PULSE_DATA.values())
                        continue
                    await client.add_pulses(Channel.A, *(pulse_data_current))
                else:
                    await client.clear_pulses(Channel.A)
            except :
                print("das")



       
        

if __name__ == "__main__":
    asyncio.run(main())
    
    
    



