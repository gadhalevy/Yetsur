import cv2 ,numpy as np,openpyscad as ops

''' 
Get disired place for ktav by mouse lbutton.
'''
class Crop:
    """
    Draws rect with mouse, to find coordinates and scale of text.
    Operate:instance.main(pathRead,pathWrite)
    parameters:
    pathRead raw image
    pathWrite cropped image
    left button draws rectangle
    right button return startX,endX,startY,endY
    """

    def draw_rect(self,event,x,y,flags,param):
        # if event == cv2.EVENT_LBUTTONDOWN:
        #     self.ix,self.iy = x,y
        # elif event == cv2.EVENT_LBUTTONUP:
        #     cv2.rectangle(self.img, (self.ix, self.iy), (x, y), (0, 255, 0), 1)
        # elif event==cv2.EVENT_RBUTTONDBLCLK:
        #     del(self.img)
        #     self.img = cv2.imread(param)
        # elif event==cv2.EVENT_RBUTTONDOWN:
        #     sortx=sorted([x,self.ix])
        #     sorty=sorted([y,self.iy])
        #     self.span= int(sorty[0])//2,int(sorty[1])//2,int(sortx[0])//2,int(sortx[1])//2
        if event == cv2.EVENT_LBUTTONDOWN:
            self.x,self.y=x,y
    def main(self,img):
        """
        :param pathRead:
        :param pathWrite:
        :return:
        """
        self.img = cv2.resize(img,(img.shape[0]*2,img.shape[1]*2))
        cv2.namedWindow('image')
        cv2.setMouseCallback('image',self.draw_rect)
        while True:
            cv2.imshow('image',self.img)
            self.k = cv2.waitKey(1) & 0xFF
            if self.k == 27:
                break
        cv2.destroyAllWindows()
        return int(self.x/2),int(self.y/2)
class Cnc:
    def __init__(self,pic,file):
        '''
        Reads image and resizes it to the size of the raw block material 90,50
        Takes contours from image, and
        :argument
        '''
        self.file=file
        self.hight=90
        self.width=50
        self.thick=15
        # Read image
        self.orig = cv2.imread(pic)
        # If image orientation is portrait
        if self.orig.shape[0]>self.orig.shape[1]:
            # Resize to portrait
            self.im=cv2.resize(self.orig,(self.width,self.hight))
            self.portrait=True
        # Else
        else:
            # Resize to landscape
            self.im=cv2.resize(self.orig,(self.hight,self.width))
            self.portrait=False
        # Convert image to gray.
        imgray = cv2.cvtColor(self.im, cv2.COLOR_BGR2GRAY)
        # Threshold the image with correct threshold parameter.
        ret, self.thresh = cv2.threshold(imgray, 127, 255, cv2.THRESH_BINARY_INV)
        # Find image contours.
        self.contours, hierarchy = cv2.findContours(self.thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        # Initial code for milling.
        self.txt1='''
         m6 t3 
         T01 ( TOOL NAME: 3   )
         N10 G54 G90 G00 X0 Y0 S2000 M03
         Z50.
         '''
        # Gcode for entering the mill block.
        self.txt2='''
         Z2.
         Z1.
         G01 Z-2. F105
        '''
        # Gcode for exiting the mill block.
        self.txt3='''
         G00 Z2.
         Z50.
         '''
        self.txt7 = '''
         Z2.
         Z1.
         G01 Z-3. F105
        '''


    def show(self):
        '''
        Show all contours the user selects the best contour for printing by its number.
        :return:
        '''
        # Declare dictionary
        dic={}
        # Loop all the enumerate contours
        for n,c in enumerate (self.contours):
            # Set dictionary key as img# num and value as acopy of the image
            dic['img%s'%str(n)]=self.im.copy()
            # Draw each contour separately
            cv2.drawContours(dic['img%s'%str(n)],[c],0,(0,255,0),1)
            # Write the number of the contour on the image
            cv2.putText(dic['img%s'%str(n)],str(n),(20,20),cv2.FONT_HERSHEY_SIMPLEX,1,(255,0,0),2)
            # Show it
            cv2.imshow('img%s' %str(n),dic['img%s'%str(n)])
        # Wait for user to choose the number.
        w=cv2.waitKey(0)
        # Store that number as class variable
        self.the_contour=int(chr(w))
        # Destroy all windows.
        cv2.destroyAllWindows()
        # Flatten the chosen contour for milling.
        self.flat=np.array(self.contours[self.the_contour]).ravel()

    def make_3Dprint(self,size,txt,x_start,y_start):
        '''
        Take chosen contour from show method, makes polygon with openscad from it,
        extrude it to desired thickness and writes it to a scad file.
        parameter: File name of output file.
        :return:
        '''
        self.txt4 = '''
                module base(){        
                '''
        self.txt5 = '''
                module t(t, size=%d, style="")
            {
                linear_extrude( 3 )
            text(t, size, font=str("Liberation Sans", style), valign="center", halign="center");
            };''' % (int(size))
        self.txt6 = '''
                module super(){
            base();
            translate([ %d, %d, %d])
            color("purple")t("%s");
        };
        super();''' % (x_start, y_start, int(self.thick / 2), txt)
        self.txt = txt
       # Declare list of points.
        points = []
        # Loop all points of chosen contour.
        for c in self.contours[self.the_contour]:
            # Add point of contour to list of points
            points.append(list(c[0]))
        # Construct poligon
        p = ops.Polygon(points=points)
        # # linear extrude the poligon to material thickness.
        le = p.linear_extrude(self.thick)
        # center model in z axe.
        le = le.translate([0, 0, -int(self.thick / 2)])
        with open(self.file+'.scad','w') as f:
            f.write(self.txt4+'\n')
            f.write(str(le)+'\n')
            f.write('};'+'\n')
            f.write(self.txt5+'\n')
            f.write(self.txt6+'\n')

    def sketch(self):
        '''
        Write a gcode milling file of the chosen contour.
        :argument Output file name.
        '''
        # Open file for writing.
        with open(self.file+'.sketch','w') as w:
            # Write initial milling code
            w.write(self.txt1)
            # Gcode run in fast mode to start point of the chosen contour 10 mm above material and operate flood mode M8
            w.write('G00 X%s Y%s Z10 M8' %(self.flat[0],self.flat[1]))
            # Gcode enter the mill block
            w.write(self.txt2)
            # Loop every second item in flatten contour
            for i in range(2,len(self.flat),2):
                # Write as Gcode the contour x and y
                w.write(' X'+str(self.flat[i])+' Y'+str(self.flat[i+1])+'\n')
            # Write Gcode for exit the milling block.
            w.write(self.txt3)

    def make_txt(self,x0,y0):
        len_txt=len(self.txt)*7 #size of a letter in openscad
        scale=2
        size = cv2.getTextSize(self.txt, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        while size[0][0]>len_txt:
            scale-=0.1
            size = cv2.getTextSize(self.txt, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        if self.portrait==True:
            blank_image = np.zeros((self.hight, self.width, 3), np.uint8)
        else:
            blank_image = np.zeros((self.width, self.hight, 3), np.uint8)
        # blank_image=np.zeros((size[0],size[1],3), np.uint8)
        org = (x0 - int(size[0][0] / 2), y0 + int(size[0][1] / 2))
        # print(x0,y0,org,scale)
        ktav=cv2.putText(blank_image,self.txt,org,cv2.FONT_HERSHEY_SIMPLEX,scale,(255,255,255),1)
        imgray = cv2.cvtColor(ktav, cv2.COLOR_BGR2GRAY)
        # Threshold the image with correct threshold parameter.
        ret, self.thresh = cv2.threshold(imgray, 127, 255, cv2.THRESH_BINARY)
        cv2.imshow('s', self.thresh)
        roi=self.thresh[org[1]-size[0][1]:org[1],org[0]:org[0]+size[0][0]]
        roi=cv2.flip(roi,0)
        self.thresh[org[1] - size[0][1]:org[1], org[0]:org[0] + size[0][0]]=roi
        # M=cv2.getRotationMatrix2D((x0,y0),180,1)
        # self.thresh=cv2.warpAffine(self.thresh,M,(self.thresh.shape[1],self.thresh.shape[0]))
        cv2.imshow('f',self.thresh)
        # # self.thresh = cv2.flip(self.thresh, 0)
        # # cv2.imshow('f', self.thresh)
        cv2.waitKey(0)
        self.base(True)



    def base(self,kituv=False):
        '''
        Write a Gcode milling file of the base for the 3D printing.
        :argument  Output of milling file
        '''
        # Convert the threshold image to numpy array.
        self.thresh = np.array(self.thresh)
        if kituv==False:
            enter_block=self.txt2
        else:
            enter_block=self.txt7
        # State machine state=0
        state=0
        # Open file for writing.
        with open(self.file,'a') as w:
            # Write initial milling code
            if kituv==False:
                w.write(self.txt1)
            # Loop x axis
            for x in range(self.thresh.shape[0]):
                # Loop y axis
                for y in range(self.thresh.shape[1]):
                    # If state machine state is 0
                    if state==0:
                        # If threshed image pixel is white (255)
                        if self.thresh[x,y]==255:
                            # Gcode run in fast mode to start point of the chosen contour 10 mm above material and operate flood mode M8
                            w.write('G00 X%s Y%s Z10 M8' % (y, x))
                            # Gcode enter the mill block
                            w.write(enter_block)
                            # Gcode write y,x coordinates
                            w.write(' X'+str(y)+' Y'+str(x)+'\n')
                            # State machine state=1
                            state=1
                    # If state machine state is 1
                    elif state==1:
                        # If threshed image pixel is black (0)
                        if self.thresh[x,y]==0:
                            # Gcode write y,x coordinates
                            w.write(' X'+str(y)+' Y'+str(x)+'\n')
                            w.write('G00 Z10')
                            # State machine state=0
                            state=0
            # Write Gcode for exit the milling block.
            w.write(self.txt3)

def main():
    cnc=Cnc('/home/cimlab/Pictures/tau.jpeg','try')
    # cnc=Cnc('C:/Users/cimlab/Pictures/TAU.jpg','GH')
    cnc.show()
    # # cnc.sketch('contour')
    # cnc.make_3Dprint('balagan')
    crop=Crop()
    x,y=crop.main(cnc.orig)
    print('x=',x,'y=',y)
    if cnc.portrait==True:
        w=50
        h=90
    else:
        w=90
        h=50
    x0=int(x*w/cnc.orig.shape[0])
    y0=int(y*h/cnc.orig.shape[1])
    print('x0=',x0,'y0=',y0)
    cnc.make_3Dprint(4,"Gad",x0,y0)
    cnc.base()
    # # cnc.smart_base()
    cnc.make_txt(x0,y0)

main()
