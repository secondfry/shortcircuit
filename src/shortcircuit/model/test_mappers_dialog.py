# test_mappers_dialog.py
"""The Mappers dialog's type picker and table."""

import os

# The suite is headless: select the Qt platform plugin before Qt is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6 import QtWidgets

from shortcircuit.model.mapper_config import TYPE_EVESCOUT, TYPE_TRIPWIRE, MapperConfig


@pytest.fixture(scope="session")
def qapp():
  app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
  yield app


def test_picker_lists_every_type_with_a_description(qapp):
  from shortcircuit.app import MAPPER_TYPE_DESCRIPTIONS, MAPPER_TYPE_LABELS, AddMapperTypeDialog

  picker = AddMapperTypeDialog()
  rows = [picker.list_types.item(i) for i in range(picker.list_types.count())]
  assert len(rows) == len(MAPPER_TYPE_LABELS)
  for type_key in MAPPER_TYPE_LABELS:
    assert MAPPER_TYPE_DESCRIPTIONS.get(type_key), "every type needs a description"
  assert picker.selected_type() == list(MAPPER_TYPE_LABELS)[0]
  picker.list_types.setCurrentRow(1)
  assert picker.selected_type() == list(MAPPER_TYPE_LABELS)[1]


def test_details_column_never_shows_secrets(qapp):
  from shortcircuit.app import MappersDialog

  tripwire = MapperConfig(type=TYPE_TRIPWIRE, name="Corp", url="https://tw", user="pilot", password="hunter2")
  no_account = MapperConfig(type=TYPE_TRIPWIRE, name="Empty", url="https://tw")
  scout = MapperConfig(type=TYPE_EVESCOUT, name="Eve Scout")
  assert MappersDialog._cfg_details(tripwire) == "user: pilot"
  assert MappersDialog._cfg_details(no_account) == "no account set"
  assert MappersDialog._cfg_details(scout) == "public"
  for cfg in (tripwire, no_account, scout):
    assert "hunter2" not in MappersDialog._cfg_details(cfg)


def test_table_has_details_column_and_no_row_numbers(qapp):
  from shortcircuit.app import MappersDialog

  configs = [
    MapperConfig(type=TYPE_TRIPWIRE, name="Corp", url="https://tw", user="pilot", password="x"),
    MapperConfig(type=TYPE_EVESCOUT, name="Eve Scout", url="https://scout"),
  ]
  dialog = MappersDialog(configs, proxy="")
  table = dialog.tableWidget_mappers
  headers = [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]
  assert headers == ["Enabled", "Name", "Type", "Details", "URL"]
  assert table.item(0, MappersDialog.COL_DETAILS).text() == "user: pilot"
  assert table.item(1, MappersDialog.COL_URL).text() == "https://scout"
  assert not table.showGrid()
  assert not table.verticalHeader().isVisible()
