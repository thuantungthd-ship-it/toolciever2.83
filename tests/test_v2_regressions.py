import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import engine_v2 as engine  # noqa: E402


class FakeWorksheet:
    def __init__(self, headers):
        self.values = [list(headers)]
        self.update_calls = 0
        self.append_calls = 0

    def row_values(self, row_number):
        if row_number < 1 or row_number > len(self.values):
            return []
        return ["" if v is None else str(v) for v in self.values[row_number - 1]]

    def get_all_values(self):
        return [["" if v is None else str(v) for v in row] for row in self.values]

    def get_all_records(self):
        if not self.values:
            return []
        headers = [str(v).strip() for v in self.values[0]]
        result = []
        for row in self.values[1:]:
            if not any(str(v).strip() for v in row):
                continue
            result.append({h: (row[i] if i < len(row) else "") for i, h in enumerate(headers) if h})
        return result

    def append_rows(self, rows, value_input_option=None):
        self.append_calls += 1
        for row in rows:
            self.values.append(list(row))

    def batch_update(self, updates, value_input_option=None):
        import re

        def col_number(letters):
            value = 0
            for ch in letters.upper():
                value = value * 26 + ord(ch) - ord("A") + 1
            return value

        for update in updates:
            cell_range = update["range"]
            match = re.fullmatch(r"([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?", cell_range)
            if not match:
                raise AssertionError(f"Unsupported test range: {cell_range}")
            start_col = col_number(match.group(1))
            start_row = int(match.group(2))
            end_col = col_number(match.group(3) or match.group(1))
            end_row = int(match.group(4) or match.group(2))
            matrix = update["values"]
            for row_offset, matrix_row in enumerate(matrix):
                row_number = start_row + row_offset
                while len(self.values) < row_number:
                    self.values.append([])
                row = self.values[row_number - 1]
                for col_offset, cell_value in enumerate(matrix_row):
                    col_index = start_col + col_offset
                    if col_index > end_col:
                        break
                    while len(row) < col_index:
                        row.append("")
                    row[col_index - 1] = cell_value


class FakeSpreadsheet:
    def __init__(self):
        self.sheets = {
            "Branches": FakeWorksheet(engine.BRANCH_HEADERS),
            "Students": FakeWorksheet(engine.STUDENT_HEADERS),
            "Assessments": FakeWorksheet(engine.ASSESSMENT_HEADERS),
            "Analysis": FakeWorksheet(engine.ANALYSIS_HEADERS),
            "Settings": FakeWorksheet(engine.SETTINGS_HEADERS),
        }
        self.add_calls = 0

    def worksheet(self, title):
        if title not in self.sheets:
            raise KeyError(title)
        return self.sheets[title]

    def add_worksheet(self, *args, **kwargs):
        self.add_calls += 1
        raise AssertionError("V2 must not create new Google Sheets tabs")


def standard_student(date_text="07/09/2026-09/09/2026"):
    return {
        "name": "Nguyen Van Demo",
        "type": "standard",
        "class_info": {"sheet": "KET1", "lop": "KET1", "ngay_thi": date_text, "giaovien": "GV Demo"},
        "cc": 8.0,
        "cc_weight": 10.0,
        "cc_breakdown": None,
        "skills": [
            {"name": "Nghe", "raw": 18, "max": 25, "weight": 25, "pct_contrib": 18.0, "norm10": 7.2},
            {"name": "Nói", "raw": 23, "max": 30, "weight": 25, "pct_contrib": 19.2, "norm10": 7.67},
            {"name": "Đọc", "raw": 16, "max": 20, "weight": 20, "pct_contrib": 16.0, "norm10": 8.0},
            {"name": "Viết", "raw": 10, "max": 15, "weight": 20, "pct_contrib": 13.3, "norm10": 6.67},
        ],
        "total": 82.5,
        "grade": "B",
        "weak_skills": ["Viết"],
        "development": engine.empty_development(),
    }


def history_row(date_text, overall, speaking, *, status="ACTIVE", assessment_type="Final"):
    # Compact existing Google Sheet schema with identity metadata joined as load_google_history does.
    return {
        "branch_id": "CIE-TDM",
        "source": "CENTER",
        "name": "Nguyen Van Demo",
        "class": "KET1",
        "assessment_date": date_text,
        "assessment_type": assessment_type,
        "listening": 7.0,
        "speaking": speaking,
        "reading": 8.0,
        "writing": 6.0,
        "overall_score": overall,
        "weakest_skill": "Viết",
        "overall_level": "B",
        "final_status": status,
        "student_id": "CIE-TDM-C-DEMO-KET1-ABCDE",
    }


class V2RegressionTests(unittest.TestCase):
    def test_date_ranges_without_spaces_parse_and_use_end_date(self):
        self.assertEqual(
            engine._split_exam_dates("07/09/2026-09/09/2026"),
            ("2026-09-07", "2026-09-09"),
        )
        self.assertEqual(
            engine._split_exam_dates("07/09/2026 - 09/09/2026"),
            ("2026-09-07", "2026-09-09"),
        )
        self.assertEqual(engine._parse_history_date("07/09/2026-09/09/2026").isoformat(), "2026-09-09")
        self.assertEqual(engine._parse_history_date("2026-10-09").isoformat(), "2026-10-09")

    def test_upload_filename_does_not_change_logical_key(self):
        key_a = engine._assessment_logical_key(
            "CIE-TDM", "CENTER", "Nguyen Van Demo", "KET1",
            "07/09/2026-09/09/2026", "Final",
        )
        key_b = engine._assessment_logical_key(
            "CIE-TDM", "CENTER", "Nguyen Van Demo", "KET1",
            "2026-09-07 – 2026-09-09", "Final",
        )
        self.assertEqual(key_a, key_b)

    def test_reupload_67_same_scores_does_not_append_duplicate_rows(self):
        db = FakeSpreadsheet()
        students = []
        for i in range(67):
            student = standard_student()
            student["name"] = f"Nguyen Van Demo {i + 1:02d}"
            students.append(student)

        result1 = self._sync_many(db, students, source_file="/tmp/random-a/score.xlsx")
        count_after_first = len(db.worksheet("Assessments").get_all_records())
        result2 = self._sync_many(db, students, source_file="/tmp/random-b/score.xlsx")
        result3 = self._sync_many(db, students, source_file="another-name.xlsx")

        self.assertEqual(result1["new"], 67)
        self.assertEqual(result2["new"], 0)
        self.assertEqual(result2["existing"], 67)
        self.assertEqual(result3["new"], 0)
        self.assertEqual(len(db.worksheet("Assessments").get_all_records()), count_after_first)
        self.assertEqual(count_after_first, 67)
        self.assertEqual(len(db.worksheet("Students").get_all_records()), 67)
        self.assertEqual(len(db.worksheet("Analysis").get_all_records()), 67)
        self.assertEqual(db.add_calls, 0)

    def test_changed_scores_replace_old_version_without_deleting_history(self):
        db = FakeSpreadsheet()
        student = standard_student()
        self._sync(db, student, source_file="old.xlsx")
        changed = copy.deepcopy(student)
        changed["total"] = 88.0
        changed["grade"] = "B+"
        changed["skills"][1]["norm10"] = 8.6
        result = self._sync(db, changed, source_file="new-temp-name.xlsx")
        rows = db.worksheet("Assessments").get_all_records()
        statuses = [r["final_status"] for r in rows]
        self.assertEqual(len(rows), 2)
        self.assertIn("REPLACED", statuses)
        self.assertEqual(statuses.count("ACTIVE"), 1)
        self.assertEqual(result["changed"], 1)

    def test_history_uses_prior_date_and_excludes_current_and_future(self):
        student = standard_student("01/10/2026")
        student["branch_id"] = "CIE-TDM"
        student["source"] = "CENTER"
        previous = history_row("07/09/2026-09/09/2026", 78.0, 6.7)
        same_current = history_row("01/10/2026", 82.5, 7.67)
        future = history_row("07/11/2026-09/11/2026", 91.0, 9.0)

        result = engine.analyze_development(student, [previous, same_current, future])
        self.assertEqual(result["history_count"], 1)
        self.assertEqual(result["previous"]["date"], "2026-09-09")
        # Stored 0-10 skill values are normalized to percentage points for trend analysis.
        self.assertAlmostEqual(result["skill_changes"]["Nói"], 9.7, places=2)  # current norm10 7.67 -> 76.7
        self.assertAlmostEqual(result["trend"], 4.5, places=2)
        self.assertEqual(engine._history_skills({"overall_level": "B", "speaking": 7.7})["Nói"], 77.0)
        self.assertEqual(engine._history_skills({"overall_level": "B", "speaking": 77.0})["Nói"], 77.0)

    def test_t8_t7_t8_upload_order_uses_t7_as_previous(self):
        t7 = standard_student("15/07/2026")
        t7["branch_id"] = "CIE-TDM"
        t7["source"] = "CENTER"
        t7["total"] = 72.0

        t8 = standard_student("15/08/2026")
        t8["branch_id"] = "CIE-TDM"
        t8["source"] = "CENTER"
        t8["total"] = 82.5

        # First upload T8: nothing older exists.
        self.assertEqual(engine.analyze_development(t8, [])["history_count"], 0)

        # Upload T7 after T8: T8 is a future record for T7 and must be ignored.
        t8_row = history_row("15/08/2026", 82.5, 7.67)
        self.assertEqual(engine.analyze_development(t7, [t8_row])["history_count"], 0)

        # Re-upload T8: the old T8 row is the current logical assessment and must be excluded;
        # T7 is the nearest prior dated assessment and becomes Previous.
        t7_row = history_row("15/07/2026", 72.0, 6.0)
        result = engine.analyze_development(t8, [t8_row, t7_row])
        self.assertEqual(result["history_count"], 1)
        self.assertEqual(result["previous"]["date"], "2026-07-15")
        self.assertAlmostEqual(result["trend"], 10.5, places=2)

    def test_repeat_current_assessment_refreshes_analysis_after_history_arrives(self):
        db = FakeSpreadsheet()
        t8 = standard_student("15/08/2026")
        t8["branch_id"] = "CIE-TDM"
        t8["source"] = "CENTER"
        t8["development"] = engine.empty_development()
        self._sync(db, t8, source_file="first-temp-path.xlsx")

        assessment_rows = db.worksheet("Assessments").get_all_records()
        t8_id = assessment_rows[0]["assessment_id"]
        analysis_ws = db.worksheet("Analysis")
        t8_analysis_index = next(
            i for i, row in enumerate(analysis_ws.get_all_records(), start=2)
            if row["assessment_id"] == t8_id
        )
        first_comment = analysis_ws.get_all_records()[0]["speaking_comment"]
        self.assertNotIn("so với lần đánh giá trước", first_comment)

        # Upload July after August; July must not use August as previous.
        t7 = standard_student("15/07/2026")
        t7["branch_id"] = "CIE-TDM"
        t7["source"] = "CENTER"
        t7["total"] = 72.0
        t7["grade"] = "C"
        t7["skills"][1]["norm10"] = 6.0
        t7_history = engine.load_google_history(db)
        t7["development"] = engine.analyze_development(t7, t7_history)
        self.assertEqual(t7["development"]["history_count"], 0)
        self._sync(db, t7, source_file="july-upload.xlsx")

        # Re-upload August unchanged; it must compare to July and refresh Analysis
        # in place instead of appending a duplicate assessment or analysis row.
        t8_retry = copy.deepcopy(t8)
        t8_retry["development"] = engine.analyze_development(
            t8_retry, engine.load_google_history(db)
        )
        self.assertEqual(t8_retry["development"]["previous"]["date"], "2026-07-15")
        result = self._sync(db, t8_retry, source_file="renamed-temp-path.xlsx")

        self.assertEqual(result["new"], 0)
        self.assertEqual(result["existing"], 1)
        self.assertEqual(len(db.worksheet("Assessments").get_all_records()), 2)
        self.assertEqual(len(analysis_ws.get_all_records()), 2)
        updated_rows = analysis_ws.get_all_records()
        t8_updated = next(row for row in updated_rows if row["assessment_id"] == t8_id)
        self.assertNotEqual(t8_updated["speaking_comment"], first_comment)
        self.assertIn("tăng 16.7 điểm phần trăm", t8_updated["speaking_comment"])
        self.assertEqual(t8_analysis_index, 2)

    def test_first_assessment_comments_use_current_score_without_ielts_inference(self):
        standard_comment = engine._skill_comment("Nói", 78.0, None, False)
        self.assertIn("hiện ở mức khá", standard_comment)
        self.assertNotIn("IELTS", standard_comment)
        self.assertNotIn("chưa có đủ dữ liệu", standard_comment)

        ielts_comment = engine._skill_comment("Speaking", 6.5, None, True)
        self.assertIn("hiện ở mức tốt", ielts_comment)

    def test_e_class_other_comments_only_include_speaking(self):
        student = standard_student()
        student["skills"] = [
            {"name": "Nói", "raw": 24, "max": 30, "weight": 90, "pct_contrib": 72.0, "norm10": 8.0}
        ]
        student["total"] = 80.0
        student["grade"] = "B"
        doc = engine.build_phieu(student)
        report_text = "\n".join(cell.text for table in doc.tables for row in table.rows for cell in row.cells)
        self.assertIn("Nói (Speaking)", report_text)
        self.assertNotIn("Nghe (Listening)", report_text)
        self.assertNotIn("Đọc (Reading)", report_text)
        self.assertNotIn("Viết (Writing)", report_text)

    def test_standard_report_keeps_three_tables_other_comments_and_signatures(self):
        doc = engine.build_phieu(standard_student())
        text = "\n".join(p.text for p in doc.paragraphs)
        text += "\n" + "\n".join(
            cell.text for table in doc.tables for row in table.rows for cell in row.cells
        )
        self.assertIn("1. ĐÁNH GIÁ CỦA GIÁO VIÊN", text)
        self.assertIn("2. KẾT QUẢ BÀI THI", text)
        self.assertIn("3. KẾT QUẢ CUỐI KHÓA", text)
        self.assertIn("Nhận xét khác (Other comments)", text)
        self.assertIn("Trưởng bộ phận học vụ", text)
        self.assertIn("Người lập", text)
        self.assertIn("Chữ ký GVCN", text)

    def test_sheet_guard_does_not_create_tabs_or_modify_headers(self):
        db = FakeSpreadsheet()
        ws = db.worksheet("Assessments")
        before = copy.deepcopy(ws.values)
        self.assertIs(engine._ensure_worksheet(db, "Assessments", engine.ASSESSMENT_HEADERS), ws)
        self.assertEqual(ws.values, before)
        self.assertEqual(ws.update_calls, 0)
        self.assertEqual(db.add_calls, 0)
        with self.assertRaises(RuntimeError):
            engine._ensure_worksheet(db, "NewSheet", ["x"])
        self.assertEqual(db.add_calls, 0)

    @staticmethod
    def _sync(db, student, source_file):
        return V2RegressionTests._sync_many(db, [student], source_file)

    @staticmethod
    def _sync_many(db, students, source_file):
        return engine.sync_students_to_google_sheet(
            db, copy.deepcopy(students), source_file=source_file,
            operator="IT test", branch_id="CIE-TDM", data_source="CENTER",
            assessment_type="Final",
        )


if __name__ == "__main__":
    unittest.main()
