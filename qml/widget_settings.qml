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
            to: 20
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

    // 分隔线
    Rectangle {
        Layout.fillWidth: true
        Layout.topMargin: 4
        Layout.bottomMargin: 4
        height: 1
        color: Colors.proxy.dividerColor || "#20000000"
    }

    SettingCard {
        Layout.fillWidth: true

        icon.name: "ic_fluent_resize_20_regular"
        title: qsTr("组件宽度")
        description: qsTr("新闻组件的宽度（默认 320）")

        SpinBox {
            id: widthSpin
            from: 200
            to: 500
            stepSize: 10
            onValueChanged: {
                if (settings && widthSpin.enabled)
                    settings.widget_width = Math.round(widthSpin.value)
            }
            Component.onCompleted: {
                widthSpin.value = (settings && settings.widget_width !== undefined) ? settings.widget_width : 320
            }
        }
    }

    SettingCard {
        Layout.fillWidth: true

        icon.name: "ic_fluent_resize_20_regular"
        title: qsTr("组件高度")
        description: qsTr("新闻组件的高度（默认 280）")

        SpinBox {
            id: heightSpin
            from: 150
            to: 500
            stepSize: 10
            onValueChanged: {
                if (settings && heightSpin.enabled)
                    settings.widget_height = Math.round(heightSpin.value)
            }
            Component.onCompleted: {
                heightSpin.value = (settings && settings.widget_height !== undefined) ? settings.widget_height : 280
            }
        }
    }

    SettingCard {
        Layout.fillWidth: true

        icon.name: "ic_fluent_text_paragraph_20_regular"
        title: qsTr("列表项高度")
        description: qsTr("每条新闻的高度（默认 38）")

        SpinBox {
            id: itemHeightSpin
            from: 28
            to: 60
            stepSize: 2
            onValueChanged: {
                if (settings && itemHeightSpin.enabled)
                    settings.item_height = Math.round(itemHeightSpin.value)
            }
            Component.onCompleted: {
                itemHeightSpin.value = (settings && settings.item_height !== undefined) ? settings.item_height : 38
            }
        }
    }
}
