import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RinUI
import ClassWidgets.Plugins

PluginPage {
    id: root
    title: qsTr("今日新闻")
    horizontalPadding: 0
    wrapperWidth: width - 42 * 2

    // backend 为插件本体（PluginBackendBridge 注册对象），
    // 新闻后端通过 getBackend() 获取
    property var newsBackend: root.backend ? root.backend.getBackend() : null
    property string lastUpdated: ""

    onNewsBackendChanged: refreshStatus()

    function refreshStatus() {
        if (newsBackend && newsBackend.getData) {
            let d = newsBackend.getData()
            if (d && d.updated) root.lastUpdated = d.updated
        }
    }

    Connections {
        target: root.newsBackend
        function onDataChanged(d) {
            if (d && d.updated) root.lastUpdated = d.updated
        }
    }

    Component.onCompleted: refreshStatus()

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4

        SettingCard {
            Layout.fillWidth: true

            icon.name: "ic_fluent_clock_20_regular"
            title: qsTr("自动刷新间隔")
            description: qsTr("每隔多少分钟自动获取最新新闻（最短 10 分钟）")

            SpinBox {
                id: intervalSpin
                from: 10
                to: 180
                stepSize: 5
                value: root.newsBackend ? root.newsBackend.getRefreshInterval() : 30
                onValueChanged: {
                    if (root.newsBackend && intervalSpin.enabled)
                        root.newsBackend.setRefreshInterval(Math.round(value))
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true

            icon.name: "ic_fluent_alert_20_regular"
            title: qsTr("新闻更新通知")
            description: qsTr("抓取到新头条时发送桌面通知")

            Switch {
                id: notifySwitch
                checked: root.newsBackend ? root.newsBackend.getNotifyOnUpdate() : true
                onCheckedChanged: {
                    if (root.newsBackend)
                        root.newsBackend.setNotifyOnUpdate(notifySwitch.checked)
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true

            icon.name: "ic_fluent_arrow_sync_20_regular"
            title: qsTr("立即刷新")
            description: qsTr("立即获取最新新闻")

            Button {
                text: qsTr("刷新")
                icon.name: "ic_fluent_arrow_sync_20_regular"
                onClicked: {
                    if (root.newsBackend) root.newsBackend.refreshNow()
                }
            }
        }

        SettingCard {
            Layout.fillWidth: true

            icon.name: "ic_fluent_info_20_regular"
            title: qsTr("数据来源")
            description: qsTr("新浪新闻接口（支持国内 / 国际分类），接口不可用时自动切换至“每日简报”")

            Text {
                text: root.lastUpdated ? qsTr("最近更新：%1").arg(root.lastUpdated) : qsTr("尚未更新")
                typography: Typography.Caption
                color: Colors.proxy.textSecondaryColor
            }
        }
    }
}
