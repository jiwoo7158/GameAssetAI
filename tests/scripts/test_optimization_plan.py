"""Advisory decisions never authorize mutation or invent a triangle budget."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from plan_static_optimization import plan_static_optimization


class OptimizationPlanTests(unittest.TestCase):
    def setUp(self):
        self.diagnostics = {"schema": "gameassetai.mesh-diagnostics.v1", "status": "ok",
            "errors": [], "basis": "base", "object": "Cube", "scene": "Scene",
            "metrics": {"triangles": 12, "polygons": 6}, "findings": [],
            "preservation_sensitive": False}

    def test_targets_and_no_mutation(self):
        before = copy.deepcopy(self.diagnostics)
        for target,status in ((None,"needs_target"),(12,"within_target"),(20,"within_target"),
                              (10,"candidate_for_copy_preview"),(0,"needs_review")):
            result=plan_static_optimization(self.diagnostics,target)
            self.assertEqual(status,result["status"])
            self.assertFalse(result["mutation_authorized"])
            self.assertIsNone(result["optimization_method"])
            self.assertEqual("not_verified",result["freshness"])
        self.assertEqual(before,self.diagnostics)

    def test_invalid_targets(self):
        for target in (True,False,-1,1.5,"10"):
            self.assertEqual("error",plan_static_optimization(self.diagnostics,target)["status"])

    def test_preservation_and_reviews(self):
        self.diagnostics["preservation_sensitive"]=True
        self.assertEqual("blocked",plan_static_optimization(self.diagnostics,10)["status"])
        self.diagnostics["preservation_sensitive"]=False
        for code,severity,status in (("modifiers_not_evaluated","review","needs_review"),
                ("zero_area_polygons","error","blocked"),
                ("triangle_budget_exceeded","error","candidate_for_copy_preview")):
            self.diagnostics["findings"]=[{"code":code,"severity":severity}]
            self.assertEqual(status,plan_static_optimization(self.diagnostics,10)["status"])

    def test_incomplete_or_failed_reports(self):
        for key in ("metrics","findings","preservation_sensitive","object","scene","errors"):
            data=copy.deepcopy(self.diagnostics)
            del data[key]
            self.assertEqual("error",plan_static_optimization(data,10)["status"])
        for key,value in (("status","error"),("basis","viewport_evaluated"),
                          ("findings",[{}]),("preservation_sensitive",1)):
            data=copy.deepcopy(self.diagnostics)
            data[key]=value
            self.assertEqual("error",plan_static_optimization(data,10)["status"])
        self.assertEqual("error",plan_static_optimization(None,10)["status"])

    def test_unverified_counts_and_empty_surface(self):
        for value in (None,True,-1,1.5):
            self.diagnostics["metrics"]["triangles"]=value
            self.assertEqual("error",plan_static_optimization(self.diagnostics,10)["status"])
        self.diagnostics["metrics"]={"triangles":0,"polygons":0}
        self.assertEqual("blocked",plan_static_optimization(self.diagnostics,10)["status"])
