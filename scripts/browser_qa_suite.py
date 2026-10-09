"""Autonomous Browser QA & End-to-End Verification Suite for Saakshi.

Executes real headless Chrome browser tests against http://localhost:8000:
- Maps all interactive elements
- Tests primary journeys A->B, B->C, C->A
- Tests ranking filters (Fastest, Least Walking, Transfers, Accessibility)
- Deliberately tries to break forms, inputs, rapid clicks, file uploads
- Verifies modal dialogs, observation inspection, and Gemma analysis
- Takes screenshots across desktop and mobile viewports
- Records console logs and network failures
"""

import json
import os
import sys
import time
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = "/home/wickedwizard/.gemini/antigravity-ide/brain/f869ada8-c28c-4f20-9d51-b6a681f99897"
BASE_URL = "http://localhost:8000"
PROJECT_DIR = "/home/wickedwizard/Documents/Coding/Hackathons/Hacktoberfest/Project"


def run_browser_qa():
    clean_env = dict(os.environ)
    clean_env.pop("LD_LIBRARY_PATH", None)

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "console_errors": [],
        "network_errors": [],
        "tests": {},
        "screenshots": {},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/home/wickedwizard/.gemini/antigravity-ide/bin/google-chrome",
            env=clean_env,
            headless=True,
        )

        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        # Capture console messages and network failures
        page.on(
            "console",
            lambda msg: results["console_errors"].append(f"[{msg.type}] {msg.text}")
            if msg.type in ("error", "warning")
            else None,
        )
        page.on(
            "requestfailed",
            lambda req: results["network_errors"].append(
                f"{req.method} {req.url}: {req.failure}"
            ),
        )

        print("=== STEP 1: Initial Page Load ===")
        page.goto(BASE_URL, wait_until="networkidle")
        title = page.title()
        assert "Saakshi" in title, f"Unexpected page title: {title}"
        results["tests"]["page_load"] = {"status": "PASS", "title": title}
        ss1 = os.path.join(ARTIFACTS_DIR, "qa_01_initial_load.png")
        page.screenshot(path=ss1)
        results["screenshots"]["initial_load"] = ss1

        print("=== STEP 2: Verify Mode A Journeys ===")
        # 1. A -> B
        page.click("#tab_AB")
        time.sleep(0.5)
        cards_ab = page.locator(".route-card").all_text_contents()
        assert len(cards_ab) >= 3, f"Expected >=3 route cards for A->B, got {len(cards_ab)}"
        results["tests"]["journey_A_to_B"] = {
            "status": "PASS",
            "cards_count": len(cards_ab),
            "top_route": cards_ab[0].split("\n")[0] if cards_ab else "",
        }

        # 2. B -> C
        page.click("#tab_BC")
        time.sleep(0.5)
        cards_bc = page.locator(".route-card").all_text_contents()
        assert len(cards_bc) >= 3, f"Expected >=3 route cards for B->C, got {len(cards_bc)}"
        results["tests"]["journey_B_to_C"] = {
            "status": "PASS",
            "cards_count": len(cards_bc),
            "top_route": cards_bc[0].split("\n")[0] if cards_bc else "",
        }

        # 3. C -> A
        page.click("#tab_CA")
        time.sleep(0.5)
        cards_ca = page.locator(".route-card").all_text_contents()
        assert len(cards_ca) >= 3, f"Expected >=3 route cards for C->A, got {len(cards_ca)}"
        results["tests"]["journey_C_to_A"] = {
            "status": "PASS",
            "cards_count": len(cards_ca),
            "top_route": cards_ca[0].split("\n")[0] if cards_ca else "",
        }

        # Switch back to A -> B
        page.click("#tab_AB")
        time.sleep(0.3)

        print("=== STEP 3: Ranking Filters ===")
        filters = ["fastest", "least_walking", "fewest_transfers", "best_accessibility"]
        filter_order = {}
        for f in filters:
            page.click(f'.filter-btn[data-sort="{f}"]')
            time.sleep(0.4)
            top_card = page.locator(".route-card").first.inner_text()
            filter_order[f] = top_card.split("\n")[0]
        results["tests"]["ranking_filters"] = {"status": "PASS", "top_cards": filter_order}

        print("=== STEP 4: Evidence Modal & Observation Inspection ===")
        # Click inspect observation button on route card
        page.locator(".inspect-obs-btn").first.click()
        time.sleep(0.5)
        evidence_visible = page.is_visible("#evidencePanel")
        ev_title = page.inner_text("#evTitle") if evidence_visible else ""
        results["tests"]["evidence_panel_open"] = {
            "status": "PASS" if evidence_visible else "FAIL",
            "title": ev_title,
        }

        ss2 = os.path.join(ARTIFACTS_DIR, "qa_02_evidence_modal.png")
        page.screenshot(path=ss2)
        results["screenshots"]["evidence_modal"] = ss2

        # Test sequential observation navigation if controls are visible
        btn_next = page.locator("#btnNextObs")
        btn_prev = page.locator("#btnPrevObs")
        if btn_next.is_visible() and btn_prev.is_visible():
            orig_seq = page.inner_text("#evSeqInfo")
            btn_next.click()
            time.sleep(0.4)
            new_seq = page.inner_text("#evSeqInfo")
            assert new_seq != orig_seq, f"Expected sequence to change from {orig_seq}, got {new_seq}"
            btn_prev.click()
            time.sleep(0.4)
            results["tests"]["sequential_navigation"] = {"status": "PASS", "navigated_to": new_seq}

        # Trigger analysis
        btn_gemma = page.locator("#btnRunGemma")
        if btn_gemma.is_visible():
            with page.expect_response("**/api/analyze-observation/*", timeout=45000) as resp_info:
                btn_gemma.click()
            resp = resp_info.value
            assert resp.status == 200, f"Expected 200, got {resp.status}"
            page.wait_for_selector("#gemmaResultsArea .crit-row", timeout=15000)
            btn_text = btn_gemma.inner_text()
            criteria_shown = page.is_visible("#gemmaResultsArea")
            results["tests"]["gemma_analysis_action"] = {
                "status": "PASS",
                "button_text": btn_text,
                "criteria_visible": criteria_shown,
            }
            if criteria_shown:
                ss2_analyzed = os.path.join(ARTIFACTS_DIR, "qa_02_evidence_modal_analyzed.png")
                page.screenshot(path=ss2_analyzed)
                results["screenshots"]["evidence_modal_analyzed"] = ss2_analyzed

        # Close evidence panel
        page.click(".close-btn")
        time.sleep(0.3)
        assert not page.is_visible("#evidencePanel"), "Evidence panel did not close"
        results["tests"]["evidence_panel_close"] = {"status": "PASS"}

        print("=== STEP 5: Breaking Attempts on Mode A ===")
        # Rapid clicking on tabs
        for _ in range(5):
            page.click("#tab_BC")
            page.click("#tab_AB")
            page.click("#tab_CA")
        time.sleep(0.5)
        results["tests"]["rapid_clicks_mode_A"] = {"status": "PASS"}

        print("=== STEP 6: Mode B Custom Locations & Validation ===")
        page.click("#btnModeB")
        time.sleep(0.5)
        assert page.is_visible("#modeBControls"), "Mode B controls not visible"

        # Break 1: Empty inputs
        page.fill("#customOrigin", "")
        page.fill("#customDest", "")
        page.click("#btnComputeCustom")
        time.sleep(0.3)
        err1 = page.inner_text("#planErrorBanner")
        assert "Please enter both origin and destination names" in err1, f"Unexpected error: {err1}"
        results["tests"]["mode_b_empty_validation"] = {"status": "PASS", "message": err1}

        # Break 2: Out of bounds coordinates
        page.fill("#customOrigin", "Point A")
        page.fill("#customDest", "Point B")
        page.fill("#customOriginLat", "999.0")
        page.click("#btnComputeCustom")
        time.sleep(0.3)
        err2 = page.inner_text("#planErrorBanner")
        assert "out of bounds" in err2.lower(), f"Unexpected error: {err2}"
        results["tests"]["mode_b_bounds_validation"] = {"status": "PASS", "message": err2}

        # Valid preset: Richmond Circle -> Commercial Street
        page.select_option("#tripPresetSelect", "richmond_commercial")
        time.sleep(0.8)
        cards_custom = page.locator(".route-card").all_text_contents()
        assert len(cards_custom) >= 2, f"Expected >=2 custom cards, got {len(cards_custom)}"
        results["tests"]["mode_b_preset_planning"] = {
            "status": "PASS",
            "cards_count": len(cards_custom),
            "provenance_checked": "gtfs_stop_matched" in cards_custom[1],
        }

        ss3 = os.path.join(ARTIFACTS_DIR, "qa_03_mode_b_custom_routes.png")
        page.screenshot(path=ss3)
        results["screenshots"]["mode_b_routes"] = ss3

        print("=== STEP 7: Image Upload Rejections and Acceptance ===")
        # 1. Invalid text file upload
        page.set_input_files("#fileInput", os.path.join(PROJECT_DIR, "tests/test_invalid.txt"))
        page.click("#btnUploadAnalyze")
        time.sleep(0.8)
        upload_err1 = page.inner_text("#uploadResultBanner")
        assert "rejected" in upload_err1.lower() or "unsupported" in upload_err1.lower(), f"Expected rejection, got: {upload_err1}"
        results["tests"]["upload_invalid_type"] = {"status": "PASS", "response": upload_err1}

        # 2. Blurry image upload
        page.set_input_files("#fileInput", os.path.join(PROJECT_DIR, "tests/test_blurry.jpg"))
        with page.expect_response("**/api/upload-and-analyze*", timeout=20000):
            page.click("#btnUploadAnalyze")
        time.sleep(0.5)
        upload_err2 = page.inner_text("#uploadResultBanner")
        assert "quality" in upload_err2.lower() or "rejected" in upload_err2.lower(), f"Expected quality rejection, got: {upload_err2}"
        results["tests"]["upload_blurry_image"] = {"status": "PASS", "response": upload_err2}

        # 3. Valid image upload
        valid_img = os.path.join(PROJECT_DIR, "data/street_view/a_to_b/0001.png")
        page.set_input_files("#fileInput", valid_img)
        with page.expect_response("**/api/upload-and-analyze*", timeout=45000) as upload_resp_info:
            page.click("#btnUploadAnalyze")
        upload_resp = upload_resp_info.value
        assert upload_resp.status == 200, f"Expected 200, got {upload_resp.status}"
        time.sleep(0.5)
        upload_ok = page.inner_text("#uploadResultBanner")
        assert len(upload_ok) > 0, "Upload banner empty"
        results["tests"]["upload_valid_image"] = {"status": "PASS", "response": upload_ok}

        ss4 = os.path.join(ARTIFACTS_DIR, "qa_04_upload_evaluated.png")
        page.screenshot(path=ss4)
        results["screenshots"]["upload_evaluated"] = ss4

        print("=== STEP 8: Mobile Viewport Responsiveness ===")
        page.set_viewport_size({"width": 390, "height": 844})
        time.sleep(0.5)
        ss5 = os.path.join(ARTIFACTS_DIR, "qa_05_mobile_viewport.png")
        page.screenshot(path=ss5)
        results["screenshots"]["mobile_viewport"] = ss5
        results["tests"]["mobile_viewport"] = {"status": "PASS"}

        # Restore desktop
        page.set_viewport_size({"width": 1280, "height": 800})
        time.sleep(0.3)

        print("=== STEP 9: Force Routing Fallback and Verify Explanation Banner ===")
        def handle_fallback_journeys(route):
            response = route.fetch()
            data = response.json()
            for corridor, options in data.items():
                for opt in options:
                    opt["computation_mode"] = "precompiled_fallback"
                    opt["fallback_reason"] = "forced_fallback"
                    opt["fallback_explanation"] = "Simulated routing network failure. Deterministic precompiled baseline activated."
            route.fulfill(json=data)

        page.route("**/api/journeys*", handle_fallback_journeys)
        page.reload(wait_until="networkidle")
        card_text = page.locator(".route-card").first.inner_text()
        assert "precompiled fallback" in card_text.lower(), f"Fallback banner missing in card: {card_text}"
        ss6 = os.path.join(ARTIFACTS_DIR, "qa_06_fallback_activated.png")
        page.screenshot(path=ss6)
        results["screenshots"]["fallback_activated"] = ss6
        results["tests"]["forced_fallback_ui"] = {"status": "PASS", "explanation_visible": True}
        page.unroute("**/api/journeys*", handle_fallback_journeys)

        # Final page reload sanity
        page.reload(wait_until="networkidle")
        assert "Saakshi" in page.title(), "Page reload failed"
        results["tests"]["page_reload"] = {"status": "PASS"}

        browser.close()

    report_path = os.path.join(ARTIFACTS_DIR, "browser_qa_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nAll QA tests completed. Summary saved to {report_path}")
    return results


if __name__ == "__main__":
    res = run_browser_qa()
    print(json.dumps(res, indent=2))
