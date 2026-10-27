import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"scripts"))
from check_affine_uv import check_affine_uv


class AffineUVTests(unittest.TestCase):
    def setUp(self):
        self.corners=[((0,0,0),(0,0)),((1,0,0),(1,0)),((1,1,0),(1,1)),((0,1,0),(0,1))]

    def test_affine_and_no_mutation(self):
        before=copy.deepcopy(self.corners)
        self.assertEqual("affine",check_affine_uv(self.corners,1e-6)["status"])
        self.assertEqual(before,self.corners)
        self.assertFalse(check_affine_uv(self.corners,1e-6)["mutation_authorized"])

    def test_nonaffine_and_discontinuous(self):
        self.corners[2]=((1,1,0),(1,0.3))
        self.assertEqual("blocked",check_affine_uv(self.corners,1e-6)["status"])
        self.corners=self.corners[:3]+[((0,0,0),(2,0))]
        self.assertEqual("blocked",check_affine_uv(self.corners,1e-6)["status"])

    def test_rotated_plane_and_nonplanarity(self):
        corners=[((x,y,x+y),(2*x+y,3*y-x)) for x,y in ((0,0),(1,0),(1,1),(0,1))]
        self.assertEqual("affine",check_affine_uv(corners,1e-6)["status"])
        corners[-1]=((0,1,2),(1,3))
        self.assertEqual("blocked",check_affine_uv(corners,1e-6)["status"])

    def test_degenerate_and_invalid(self):
        self.assertEqual("blocked",check_affine_uv([((i,0,0),(i,0)) for i in range(3)],1e-6)["status"])
        for tolerance in (None,True,0,-1,float("nan"),float("inf")):
            self.assertEqual("error",check_affine_uv(self.corners,tolerance)["status"])
        for corners in (None,[],[(None,None)]*3,[((0,0,float("nan")),(0,0))]*3):
            self.assertEqual("error",check_affine_uv(corners,1e-6)["status"])

    def test_finite_inputs_overflow_do_not_pass(self):
        huge=[((x*1e200,y*1e200,0),(x,y)) for x,y in ((0,0),(1,0),(1,1),(0,1))]
        self.assertEqual("error",check_affine_uv(huge,1e-6)["status"])

    def test_separate_uv_bound_is_not_geometry_bound(self):
        self.corners[2]=((1,1,0),(1,1.00001))
        self.assertEqual("blocked",check_affine_uv(self.corners,
                         geometry_tolerance=0.01,uv_tolerance=1e-7)["status"])
        self.assertEqual("affine",check_affine_uv(self.corners,
                         geometry_tolerance=1e-7,uv_tolerance=0.01)["status"])

    def test_separate_geometry_bound_is_not_uv_bound(self):
        self.corners[3]=((0,1,0.00001),(0,1))
        self.assertEqual("blocked",check_affine_uv(self.corners,
                         geometry_tolerance=1e-7,uv_tolerance=0.01)["status"])
        self.assertEqual("affine",check_affine_uv(self.corners,
                         geometry_tolerance=0.01,uv_tolerance=1e-7)["status"])

    def test_legacy_and_incomplete_separate_parameters(self):
        self.assertEqual(check_affine_uv(self.corners,1e-6),check_affine_uv(self.corners,
                         geometry_tolerance=1e-6,uv_tolerance=1e-6))
        for options in ({},{"geometry_tolerance":1e-6},{"uv_tolerance":1e-6},
                {"tolerance":1e-6,"uv_tolerance":1e-6},
                {"geometry_tolerance":True,"uv_tolerance":1e-6}):
            self.assertEqual("error",check_affine_uv(self.corners,**options)["status"])
