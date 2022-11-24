import cv2 ,numpy as np,openpyscad as ops
''' To do: To get exact place from user, to resize coordinates accordingly.
    Base milling to add text with opencv.
'''
class Cnc:
    def __init__(self,pic,txt,size,file):
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
        orig = cv2.imread(pic)
        # If image orientation is portrait
        if orig.shape[0]>orig.shape[1]:
            # Resize to portrait
            self.im=cv2.resize(orig,(self.width,self.hight))
            self.portrait=True
        # Else
        else:
            # Resize to landscape
            self.im=cv2.resize(orig,(self.hight,self.width))
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
        self.txt4='''
        module base(){        
        '''
        self.txt5='''
        module t(t, size=%d, style="")
    {
        linear_extrude( 3 )
    text(t, size, font=str("Liberation Sans", style), valign="center", halign="center");
    };'''%(int(size))
        self.txt6='''
        module super(){
    base();
    translate([ %d, %d, %d])
    color("purple")t("%s");
};
super();'''%(int(self.im.shape[1]/2), int(self.im.shape[0]/2),int(self.thick/2),txt)
        self.txt7='''
         Z2.
         Z1.
         G01 Z-3. F105
        '''
        self.txt=txt

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

    def make_3Dprint(self):
        '''
        Take chosen contour from show method, makes polygon with openscad from it,
        extrude it to desired thickness and writes it to a scad file.
        parameter: File name of output file.
        :return:
        '''
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

    def make_txt(self):
        size = cv2.getTextSize(self.txt, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        if self.portrait==True:
            blank_image = np.zeros((self.hight, self.width, 3), np.uint8)
            org=(int(self.width/2)-int(size[0][0]/2),int(self.hight/2)+int(size[0][1]/2))
        else:
            blank_image = np.zeros((self.width, self.hight, 3), np.uint8)
            org=(int(self.hight/2)-int(size[0][0]/2),int(self.width/2)+int(size[0][1]/2))
        ktav=cv2.putText(blank_image,self.txt,org,cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),2)
        imgray = cv2.cvtColor(ktav, cv2.COLOR_BGR2GRAY)
        # Threshold the image with correct threshold parameter.
        ret, self.thresh = cv2.threshold(imgray, 127, 255, cv2.THRESH_BINARY)
        # cv2.imshow('f',self.ktav)
        # cv2.waitKey(0)
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






cnc=Cnc('/home/cimlab/Pictures/tau.jpeg','Holy shit',3,'try')
# cnc=Cnc('C:/Users/cimlab/Pictures/TAU.jpg','GH')
# cnc.show()
# # cnc.sketch('contour')
# cnc.make_3Dprint('balagan')
cnc.base()
# cnc.smart_base()
cnc.make_txt()

