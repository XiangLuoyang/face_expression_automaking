from __future__ import print_function
import wx
import cv2
import dlib
import numpy
import tensorflow as tf
from preprocessing import preprocessing_factory
import reader
import model
import time
import os

import sys
from wx.lib.filebrowsebutton import FileBrowseButton

tf.app.flags.DEFINE_string('loss_model', 'vgg_16', 'The name of the architecture to evaluate. '
                           'You can view all the support models in nets/nets_factory.py')
tf.app.flags.DEFINE_integer('image_size', 256, 'Image size to train.')
tf.app.flags.DEFINE_string("model_file", "models/fe.ckpt-8000", "")
tf.app.flags.DEFINE_string("image_file", "output.jpg", "")

class MyApp(wx.App):
    
    def OnInit(self):
       frame = MyFrame("Hello World", (50, 60), (450, 340))
       frame.Show()
       self.SetTopWindow(frame)
       return True

class Image(wx.Frame):

    def __init__(self,image,parent=None,id=-1,pos=wx.DefaultPosition,title="表情包成果预览"):
    
        temp = image.ConvertToBitmap()

        size = temp.GetWidth(),temp.GetHeight()
        wx.Frame.__init__(self,parent,id,title,pos,size)

        panel = wx.Panel(self,-1)
        wx.StaticBitmap(parent=self,bitmap=temp)
        wx.StaticBitmap(parent=panel,bitmap=temp)

class Style():
    def main():

        FLAGS = tf.app.flags.FLAGS

        # Get image's height and width.
        height = 0
        width = 0
        with open(FLAGS.image_file, 'rb') as img:
            with tf.Session().as_default() as sess:
                if FLAGS.image_file.lower().endswith('png'):
                    image = sess.run(tf.image.decode_png(img.read()))
                else:
                    image = sess.run(tf.image.decode_jpeg(img.read()))
                height = image.shape[0]
                width = image.shape[1]
        tf.logging.info('Image size: %dx%d' % (width, height))

        with tf.Graph().as_default():
            with tf.Session().as_default() as sess:

                # Read image data.
                image_preprocessing_fn, _ = preprocessing_factory.get_preprocessing(
                    FLAGS.loss_model,
                    is_training=False)
                image = reader.get_image(FLAGS.image_file, height, width, image_preprocessing_fn)

                # Add batch dimension
                image = tf.expand_dims(image, 0)

                generated = model.net(image, training=False)
                generated = tf.cast(generated, tf.uint8)

                # Remove batch dimension
                generated = tf.squeeze(generated, [0])

                # Restore model variables.
                saver = tf.train.Saver(tf.global_variables(), write_version=tf.train.SaverDef.V1)
                sess.run([tf.global_variables_initializer(), tf.local_variables_initializer()])
                # Use absolute path
                FLAGS.model_file = os.path.abspath(FLAGS.model_file)
                saver.restore(sess, FLAGS.model_file)

                # Make sure 'generated' directory exists.
                generated_file = 'generated/res.jpg'
                if os.path.exists('generated') is False:
                    os.makedirs('generated')

                # Generate and write image data to file.
                with open(generated_file, 'wb') as img:
                    start_time = time.time()
                    img.write(sess.run(tf.image.encode_jpeg(generated)))
                    end_time = time.time()
                    tf.logging.info('Elapsed time: %fs' % (end_time - start_time))

                    tf.logging.info('Done. Please check %s.' % generated_file)


    # if __name__ == '__main__':
    #     tf.logging.set_verbosity(tf.logging.INFO)
    #     tf.app.run()
class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Face_Expression_AutoMai",
                          size=(800,500))
        menuFile = wx.Menu()
        menuFile.Append(1, "&About...")
        menuFile.AppendSeparator()
        menuFile.Append(2, "E&xit")
        menuBar = wx.MenuBar()
        menuBar.Append(menuFile, "&File")
        self.SetMenuBar(menuBar)
        self.CreateStatusBar()
        self.SetStatusText("Enjoy making face expression!")
        self.Bind(wx.EVT_MENU, self.OnAbout, id=1)
        self.Bind(wx.EVT_MENU, self.OnQuit, id=2)

        p = wx.Panel(self)

        # create the controls
        self.fbb1 = FileBrowseButton(p,
                                    labelText="选择风格图片:",
                                    fileMask="*.jpg")
        self.fbb2 = FileBrowseButton(p,
                                    labelText="选择五官源图片:",
                                    fileMask="*.jpg")
        btn = wx.Button(p, -1, "生成")
        self.Bind(wx.EVT_BUTTON, self.OnGenePic, btn)
        
        # setup the layout with sizers
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.fbb1, 1, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.fbb2, 1, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL)
        border = wx.BoxSizer(wx.VERTICAL)
        border.Add(sizer, 0, wx.EXPAND|wx.ALL, 15)
        p.SetSizer(border)

    def OnQuit(self, event):
        self.Close()
         
    def OnAbout(self, event):
        wx.MessageBox("Author: XiangLuoyang", 
                "About Face_Expreesion", wx.OK | wx.ICON_INFORMATION, self)

    def OnGenePic(self, evt):
        fileaddr1 = self.fbb1.GetValue()
        fileaddr2 = self.fbb2.GetValue()
        PREDICTOR_PATH = "C:\shape_predictor_68_face_landmarks.dat"
        SCALE_FACTOR = 1 
        FEATHER_AMOUNT = 11

        FACE_POINTS = list(range(17, 68))
        MOUTH_POINTS = list(range(48, 61))
        RIGHT_BROW_POINTS = list(range(17, 22))
        LEFT_BROW_POINTS = list(range(22, 27))
        RIGHT_EYE_POINTS = list(range(36, 42))
        LEFT_EYE_POINTS = list(range(42, 48))
        NOSE_POINTS = list(range(27, 35))
        JAW_POINTS = list(range(0, 17))
        # Points used to line up the images.
        ALIGN_POINTS = (LEFT_BROW_POINTS + RIGHT_EYE_POINTS + LEFT_EYE_POINTS +
                                    RIGHT_BROW_POINTS + NOSE_POINTS + MOUTH_POINTS)

        # Points from the second image to overlay on the first. The convex hull of each
        # element will be overlaid.
        OVERLAY_POINTS = [
            LEFT_EYE_POINTS + RIGHT_EYE_POINTS + LEFT_BROW_POINTS + RIGHT_BROW_POINTS,
            NOSE_POINTS + MOUTH_POINTS,
        ]

        # Amount of blur to use during colour correction, as a fraction of the
        # pupillary distance.
        COLOUR_CORRECT_BLUR_FRAC = 0.6

        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(PREDICTOR_PATH)

        class TooManyFaces(Exception):
            pass

        class NoFaces(Exception):
            pass

        def get_landmarks(im):
            rects = detector(im, 1)
            
            if len(rects) > 1:
                raise TooManyFaces
            if len(rects) == 0:
                raise NoFaces

            return numpy.matrix([[p.x, p.y] for p in predictor(im, rects[0]).parts()])

        def annotate_landmarks(im, landmarks):
            im = im.copy()
            for idx, point in enumerate(landmarks):
                pos = (point[0, 0], point[0, 1])
                cv2.putText(im, str(idx), pos,
                            fontFace=cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
                            fontScale=0.4,
                            color=(0, 0, 255))
                cv2.circle(im, pos, 3, color=(0, 255, 255))
            return im

        def draw_convex_hull(im, points, color):
            points = cv2.convexHull(points)
            cv2.fillConvexPoly(im, points, color=color)

        def get_face_mask(im, landmarks):
            im = numpy.zeros(im.shape[:2], dtype=numpy.float64)

            for group in OVERLAY_POINTS:
                draw_convex_hull(im,
                                landmarks[group],
                                color=1)

            im = numpy.array([im, im, im]).transpose((1, 2, 0))

            im = (cv2.GaussianBlur(im, (FEATHER_AMOUNT, FEATHER_AMOUNT), 0) > 0) * 1.0
            im = cv2.GaussianBlur(im, (FEATHER_AMOUNT, FEATHER_AMOUNT), 0)

            return im
            
        def transformation_from_points(points1, points2):
            """
            Return an affine transformation [s * R | T] such that:

                sum ||s*R*p1,i + T - p2,i||^2

            is minimized.

            """
            # Solve the procrustes problem by subtracting centroids, scaling by the
            # standard deviation, and then using the SVD to calculate the rotation. See
            # the following for more details:
            #   https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem

            points1 = points1.astype(numpy.float64)
            points2 = points2.astype(numpy.float64)

            c1 = numpy.mean(points1, axis=0)
            c2 = numpy.mean(points2, axis=0)
            points1 -= c1
            points2 -= c2

            s1 = numpy.std(points1)
            s2 = numpy.std(points2)
            points1 /= s1
            points2 /= s2

            U, S, Vt = numpy.linalg.svd(points1.T * points2)

            # The R we seek is in fact the transpose of the one given by U * Vt. This
            # is because the above formulation assumes the matrix goes on the right
            # (with row vectors) where as our solution requires the matrix to be on the
            # left (with column vectors).
            R = (U * Vt).T

            return numpy.vstack([numpy.hstack(((s2 / s1) * R,
                                            c2.T - (s2 / s1) * R * c1.T)),
                                numpy.matrix([0., 0., 1.])])

        def read_im_and_landmarks(fname):
            im = cv2.imread(fname, cv2.IMREAD_COLOR)
            im = cv2.resize(im, (im.shape[1] * SCALE_FACTOR,
                                im.shape[0] * SCALE_FACTOR))
            s = get_landmarks(im)

            return im, s

        def warp_im(im, M, dshape):
            output_im = numpy.zeros(dshape, dtype=im.dtype)
            cv2.warpAffine(im,
                        M[:2],
                        (dshape[1], dshape[0]),
                        dst=output_im,
                        borderMode=cv2.BORDER_TRANSPARENT,
                        flags=cv2.WARP_INVERSE_MAP)
            return output_im

        def correct_colours(im1, im2, landmarks1):
            blur_amount = COLOUR_CORRECT_BLUR_FRAC * numpy.linalg.norm(
                                    numpy.mean(landmarks1[LEFT_EYE_POINTS], axis=0) -
                                    numpy.mean(landmarks1[RIGHT_EYE_POINTS], axis=0))
            blur_amount = int(blur_amount)
            if blur_amount % 2 == 0:
                blur_amount += 1
            im1_blur = cv2.GaussianBlur(im1, (blur_amount, blur_amount), 0)
            im2_blur = cv2.GaussianBlur(im2, (blur_amount, blur_amount), 0)

            # Avoid divide-by-zero errors.
            im2_blur += (128 * (im2_blur <= 1.0)).astype(im2_blur.dtype)

            return (im2.astype(numpy.float64) * im1_blur.astype(numpy.float64) /
                                                        im2_blur.astype(numpy.float64))

        im1, landmarks1 = read_im_and_landmarks(fileaddr1)
        im2, landmarks2 = read_im_and_landmarks(fileaddr2)

        M = transformation_from_points(landmarks1[ALIGN_POINTS],
                                      landmarks2[ALIGN_POINTS])

        mask = get_face_mask(im2, landmarks2)
        warped_mask = warp_im(mask, M, im1.shape)
        combined_mask = numpy.max([get_face_mask(im1, landmarks1), warped_mask],
                                axis=0)

        warped_im2 = warp_im(im2, M, im1.shape)
        warped_corrected_im2 = correct_colours(im1, warped_im2, landmarks1)

        output_im = im1 * (1.0 - combined_mask) + warped_corrected_im2 * combined_mask

        cv2.imwrite('output.jpg', output_im)
        # self.sound = wx.Sound(filename)
        # if self.sound.IsOk():
        #     self.sound.Play(wx.SOUND_ASYNC)
        # else:
        #     wx.MessageBox("Invalid sound file", "Error")    

        # Alerts after generating the pictures
        image = wx.Image("./output.jpg",wx.BITMAP_TYPE_JPEG)
        frame = Image(image)
        frame.Show()
        dlg = wx.MessageDialog(None, '图片生成完毕，开始风格迁移。未迁移前图片地址："./output.jpg"',
                          'Succeed', wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        Style.main()
        image = wx.Image("./generated/res.jpg",wx.BITMAP_TYPE_JPEG)
        frame = Image(image)
        frame.Show()
app = wx.PySimpleApp()
frm = MyFrame()
frm.Show()
app.MainLoop()
