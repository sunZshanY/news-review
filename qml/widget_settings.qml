import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RinUI
import ClassWidgets.Plugins

SettingsLayout {
    id: root

    SettingCard {
        Layout.fillWidth: true

        icon.name: "ic_fluent_text_bullet_list_20_regular"
        title: qsTr("显示条数")
        description: qsTr("每个栏目最多展示的新闻条数")

        SpinBox {
            id: maxItemsSpin
            from: 3
            to: 15
            value: settings.max_items
            onValueChanged: settings.max_items = Math.round(value)
        }
    }

    SettingCard {
        Layout.fillWidth: true

        icon.name: "ic_fluent_alert_20_regular"
        title: qsTr("热度标记")
        description: qsTr("为高热度新闻显示“热”标记")

        Switch {
            id: scoreSwitch
            checked: settings.show_score
            onCheckedChanged: settings.show_score = checked
        }
    }
}
