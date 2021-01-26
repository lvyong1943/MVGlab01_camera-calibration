# author:Zhaoran ZHAO
# contact: zhaozhaoran@bupt.edu.cn
# datetime:2020/3/12 8:38 pm
# software: PyCharm

import numpy as np
from numpy import linalg as LA


class SingleCamera:

    def __init__(self, world_coor, pixel_coor, n):

        self.__world_coor = world_coor
        self.__pixel_coor = pixel_coor
        self.__point_num = n

        '''
        0. P is the appropriate form when Pm=0
        1. SVD-solved M is known up to scale, 
        which means that the true values of the camera matrix are some scalar multiple of M,
        recorded as __roM
        2. __M can be represented as form [A b], where A is a 3x3 matrix and b is with shape 3x1
        3. __K is the intrisic Camera Matrix  
        4. __R and __t for rotation and translation
        
        '''
        self.__P = np.empty([self.__point_num, 12], dtype=float)
        self.__roM = np.empty([3, 4], dtype=float)
        self.__A = np.empty([3, 3], dtype=float)
        self.__b = np.empty([3, 1], dtype=float)
        self.__K = np.empty([3, 3], dtype=float)
        self.__R = np.empty([3, 3], dtype=float)
        self.__t = np.empty([3, 1], dtype=float)

    def returnAb(self):
        return self.__A, self.__b

    def returnKRT(self):
        return self.__K, self.__R, self.__t

    def returnM(self):
        return self.__roM

    def myReadFile(filePath):
        pass

    def changeHomo(no_homo):
        pass

    # to compose P in right form s.t. we can get Pm=0
    def composeP(self):
        i = 0
        #P = np.empty([self.__point_num, 12], dtype=float)
        P = np.empty([self.__point_num*2, 12], dtype=float)
        # print(P.shape)
        while i < self.__point_num:
            c=i
            p1 = self.__world_coor[c]
            p2 = np.array([0, 0, 0, 0])
            p3 = -p1 * self.__pixel_coor[c][0]
            P[i*2] = np.hstack((p1, p2, p3))
            p3 = -p1 * self.__pixel_coor[c][1]
            P[i*2+1] = np.hstack((p2, p1, p3))
            '''
            c = i // 2
            p1 = self.__world_coor[c]
            p2 = np.array([0, 0, 0, 0])
            if i % 2 == 0:
                p3 = -p1 * self.__pixel_coor[c][0]
                #print(p3)
                P[i] = np.hstack((p1, p2, p3))

            elif i % 2 == 1:
                p3 = -p1 * self.__pixel_coor[c][1]
                #print(p3)
                P[i] = np.hstack((p2, p1, p3))
            '''
            # M = P[i]
            # print(M)
            i = i + 1
        print("Now P is with form of :")
        print(P)
        self.__P = P

    # svd to P，return A,b, where M=[A b]
    def svdP(self):
        U, sigma, VT = LA.svd(self.__P)
        # print(VT.shape)
        V = np.transpose(VT)
        preM = V[:, -1]
        roM = preM.reshape(3, 4)
        print("some scalar multiple of M,recorded as roM:")
        print(roM)
        A = roM[0:3, 0:3].copy()
        b = roM[0:3, 3:4].copy()
        print("M can be written in form of [A b],where A is 3x3 and b is 3x1, as following:")
        print(A)
        print(b)
        self.__roM = roM
        self.__A = A
        self.__b = b

    # solve the intrinsics and extrisics
    def workInAndOut(self):
        # compute ro, where ro=1/|a3|, ro may be positive or negative,
        # we choose the positive ro and name it ro01
        a3T = self.__A[2]
        # print(a3T)
        under = LA.norm(a3T)
        # print(under)
        ro01 = 1 / under
        print("The ro is %f"%ro01)

        # comput cx and cy
        a1T = self.__A[0]
        a2T = self.__A[1]
        cx = ro01 * ro01 * (np.dot(a1T, a3T))
        cy = ro01 * ro01 * (np.dot(a2T, a3T))
        print("cx=%f,cy=%f "%(cx, cy))

        # compute theta
        a_cross13 = np.cross(a1T, a3T)
        a_cross23 = np.cross(a2T, a3T)
        theta = np.arccos((-1) * np.dot(a_cross13, a_cross23) / (LA.norm(a_cross13) * LA.norm(a_cross23)))
        print("theta is: %f"%theta)

        # compute alpha and beta
        alpha = ro01 * ro01 * LA.norm(a_cross13) * np.sin(theta)
        beta = ro01 * ro01 * LA.norm(a_cross23) * np.sin(theta)
        print("alpha:%f, beta:%f"%(alpha,beta))

        # compute K
        K = np.array([alpha, -alpha * (1 / np.tan(theta)), cx, 0, beta / (np.sin(theta)), cy, 0, 0, 1])
        K = K.reshape(3, 3)
        print("We can get K accordingly: ")
        print(K)
        self.__K = K

        # compute R
        r1 = a_cross23 / LA.norm(a_cross23)
        r301 = ro01 * a3T
        r2 = np.cross(r301, r1)
        #print(r1, r2, r301)
        R = np.hstack((r1, r2, r301))
        R=R.reshape(3,3)
        print("we can get R:")
        print(R)
        self.__R = R

        # compute T
        T = ro01 * np.dot(LA.inv(K), self.__b)
        print("we can get t:")
        print(T)
        self.__t = T

    def selfcheck(self,w_check,c_check):
        my_size=c_check.shape[0]
        my_err=np.empty([my_size])
        for i in range(my_size) :
            test_pix = np.dot(self.__roM, w_check[i])
            u = test_pix[0] / test_pix[2]
            v = test_pix[1] / test_pix[2]
            u_c=c_check[i][0]
            v_c=c_check[i][1]
            print("you get test point %d with result (%f,%f)"%(i, u, v))
            print("the correct result is (%f,%f)"%(u_c,v_c))
            my_err[i]=(abs(u-u_c)/u_c+abs(v-v_c)/v_c)/2
        average_err=my_err.sum()/my_size
        print("The average error is %f ,"%average_err)
        if(average_err>0.1):
            print("which is more than 0.1")
        else:
            print("which is smaller than 0.1, the M is acceptable")



