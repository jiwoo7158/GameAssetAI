"""Offline tests for explicit independent-copy static LOD requests."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/"scripts"))
from validate_static_lod_copy_request import SCHEMA,validate_static_lod_copy_request  # noqa:E402


def fixture():
    return {"schema":SCHEMA,"scene_name":"Scene","source_object_name":"Hero_LOD0",
            "output_object_name":"Hero_LOD1","output_mesh_name":"Hero_LOD1_Mesh",
            "operation":{"method":"DECIMATE_COLLAPSE","ratio":0.5,"triangulate":False},
            "policy":{"geometry_source":"BASE_MESH_ONLY","dependency_handling":"REFUSE",
                      "source_mutation":"PRESERVE","output_independence":"NEW_OBJECT_AND_MESH",
                      "transform":"COPY_EXACT","materials":"SHARE_DATABLOCKS_READ_ONLY",
                      "uv_layers":"COPY","authorization":"PREVIEW_THEN_EXPLICIT_APPLY"}}


class StaticLodCopyRequestTests(unittest.TestCase):
    def test_exact_request_is_stable_and_read_only(self):
        request=fixture(); before=copy.deepcopy(request)
        first=validate_static_lod_copy_request(request); second=validate_static_lod_copy_request(request)
        self.assertEqual("ready",first["status"]); self.assertEqual(first,second)
        self.assertEqual(before,request); self.assertFalse(first["mutation_authorized"])

    def test_ratio_method_and_triangulation_are_explicit_and_bounded(self):
        for value in (0,0.009,1,True,float("nan"),float("inf"),"0.5"):
            request=fixture(); request["operation"]["ratio"]=value
            self.assertEqual("error",validate_static_lod_copy_request(request)["status"])
        for key,value in (("method","QUADRIFLOW"),("triangulate",True)):
            request=fixture(); request["operation"][key]=value
            self.assertEqual("error",validate_static_lod_copy_request(request)["status"])

    def test_names_must_be_explicit_and_nonoverlapping(self):
        for key,value in (("scene_name"," "),("output_object_name","Hero_LOD0"),
                          ("output_mesh_name","Hero_LOD1")):
            request=fixture(); request[key]=value
            self.assertEqual("error",validate_static_lod_copy_request(request)["status"])

    def test_fixed_preservation_policy_refuses_broader_mutation(self):
        mutations={"geometry_source":"EVALUATED","dependency_handling":"APPLY",
                   "source_mutation":"ALLOW","output_independence":"SHARED_MESH",
                   "transform":"APPLY","materials":"COPY_AND_EDIT","uv_layers":"DROP",
                   "authorization":"IMMEDIATE"}
        for key,value in mutations.items():
            request=fixture(); request["policy"][key]=value
            self.assertEqual("error",validate_static_lod_copy_request(request)["status"])

    def test_malformed_missing_and_unknown_fields_refuse_without_hash(self):
        requests=[None,[],{3:"bad"}]
        request=fixture(); request.pop("policy"); requests.append(request)
        request=fixture(); request["guess_ratio"]=True; requests.append(request)
        request=fixture(); request["operation"]["vertex_group"]="Group"; requests.append(request)
        for request in requests:
            report=validate_static_lod_copy_request(request)
            self.assertEqual("error",report["status"]); self.assertIsNone(report["request_sha256"])


if __name__=="__main__": unittest.main()
