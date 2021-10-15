# Control the ePaper display of the DGT Centaur
#
# This method uses a thread to monitor for changes to an image
# Then any alterations to the image will show on the epaper
# You can either use the image functions in this file or modify epaper.epaperbuffer directly.
from DGTCentaurMods.display import epd2in9d
import time
from PIL import Image, ImageDraw, ImageFont
import pathlib
import threading
import hashlib

font18 = ImageFont.truetype(str(pathlib.Path(__file__).parent.resolve()) + "/../resources/Font.ttc", 18)
# Screenbuffer is what we want to display on the screen
epaperbuffer = Image.new('1', (128, 296), 255) # You can also use pillow to directly change this image
lastepaperhash = 0
epaperprocesschange = 1
epd = epd2in9d.EPD()
epaperUpd = ""
kill = 0

def saveImage():
    filename = str(pathlib.Path(__file__).parent.resolve()) + "/../web/static/epaper.jpg"
    epaperbuffer.save(filename)

def epaperUpdate():
    # This is used as a thread to update the e-paper if the image has changed
    global epaperbuffer
    global lastepaperhash
    global epaperprocesschange
    global kill
    print("started epaper update thread")
    epd.display(epd.getbuffer(epaperbuffer))
    time.sleep(4)
    print("epaper init image sent")
    while True and kill == 0:
        thishash = hashlib.md5(epaperbuffer.tobytes()).hexdigest()
        if thishash != lastepaperhash and epaperprocesschange == 1:
            starttime = time.time()
            im = epaperbuffer.copy()
            saveScreenToImage = threading.Thread(target=saveImage, args=())
            saveScreenToImage.daemon = True
            saveScreenToImage.start()
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            epd.DisplayPartial(epd.getbuffer(im))
            lastepaperhash = thishash
        time.sleep(0.2)

def initEpaper():
    # Set the screen to a known start state and start the epaperUpdate thread
    global epaperbuffer
    global epaperUpd
    epaperbuffer = Image.new('1', (128, 296), 255)
    print("init epaper")
    epd.init()
    epaperUpd = threading.Thread(target=epaperUpdate, args=())
    epaperUpd.daemon = True
    epaperUpd.start()

def pauseEpaper():
    # Pause epaper updates (for example if you know you will be making a lot of changes in quick succession
    global epaperprocesschange
    time.sleep(0.3)
    epaperprocesschange = 0
    time.sleep(0.3)

def unPauseEpaper():
    # Unpause previously paused epaper
    global epaperprocesschange
    epaperprocesschange = 1

def stopEpaper():
    # Stop the epaper
    global lastepaperhash
    global lastepaperbytes
    global epaperbuffer
    global kill
    filename = str(pathlib.Path(__file__).parent.resolve()) + "/../resources/logo_mods_screen.jpg"
    #epaperbuffer = Image.new('1', (128, 296), 255)
    epaperbuffer = Image.open(filename)
    time.sleep(3)
    kill = 1
    time.sleep(0.5)
    epd.sleep()

def writeText(row,txt):
    # Write Text on a give line number
    global epaperbuffer
    nimage = epaperbuffer.copy()
    image = Image.new('1', (128, 20), 255)
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), txt, font=font18, fill=0)
    nimage.paste(image, (0, (row * 20)))
    epaperbuffer = nimage.copy()

def drawRectangle(x1, y1, x2, y2, fill, outline):
    # Draw a rectangle
    global epaperbuffer
    draw = ImageDraw.Draw(epaperbuffer)
    draw.rectangle([(x1, y1), (x2, y2)], fill=fill, outline=outline)

def clearArea(x1, y1, x2, y2):
    # Clears an area of the screen. In fact just draws a white rectangle
    drawRectangle(x1,y1,x2,y2,255,255)

def clearScreen():
    # Set the ePaper back to white
    global epaperbuffer
    epaperbuffer = Image.new('1', (128, 296), 255)

def drawBoard(pieces):
    global epaperbuffer
    chessfont = Image.open("/home/pi/centaur/fonts/ChessFontSmall.bmp")
    for x in range(0,64):
        pos = (x - 63) * -1
        row = 50 + (16 * (pos // 8))
        col = (x % 8) * 16
        px = 0
        r = x // 8
        c = x % 8
        py = 0
        if (r // 2 == r / 2 and c // 2 == c / 2):
            py = py + 16
        if (r //2 != r / 2 and c // 2 != c / 2):
            py = py + 16
        if pieces[x] == "P":
            px = 16
        if pieces[x] == "R":
            px = 32
        if pieces[x] == "N":
            px = 48
        if pieces[x] == "B":
            px = 64
        if pieces[x] == "Q":
            px = 80
        if pieces[x] == "K":
            px = 96
        if pieces[x] == "p":
            px = 112
        if pieces[x] == "r":
            px = 128
        if pieces[x] == "n":
            px = 144
        if pieces[x] == "b":
            px = 160
        if pieces[x] == "q":
            px = 176
        if pieces[x] == "k":
            px = 192
        piece = chessfont.crop((px, py, px+16, py+16))
        epaperbuffer.paste(piece,(col, row))

def promotionOptions(row):
    # Draws the promotion options to the screen buffer
    global epaperbuffer
    offset = row * 20
    draw = ImageDraw.Draw(epaperbuffer)
    draw.text((0, offset+0), "    Q    R    N    B", font=font18, fill=0)
    draw.polygon([(2, offset+18), (18, offset+18), (10, offset+3)], fill=0)
    draw.polygon([(35, offset+3), (51, offset+3), (43, offset+18)], fill=0)
    o = 66
    draw.line((0+o,offset+16,16+o,offset+16), fill=0, width=5)
    draw.line((14+o,offset+16,14+o,offset+5), fill=0, width=5)
    draw.line((16+o,offset+6,4+o,offset+6), fill=0, width=5)
    draw.polygon([(8+o, offset+2), (8+o, offset+10), (0+o, offset+6)], fill=0)
    o = 97
    draw.line((6+o,offset+16,16+o,offset+4), fill=0, width=5)
    draw.line((2+o,offset+10, 8+o,offset+16), fill=0, width=5)
