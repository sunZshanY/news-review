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

        // 数据源设置
        SettingCard {
            Layout.fillWidth: true

            icon.name: "ic_fluent_globe_20_regular"
            title: qsTr("数据源")
            description: qsTr("选择新闻数据来源")

            ComboBox {
                id: sourceCombo
                width: 160
                model: [qsTr("默认（新浪新闻）"), qsTr("自定义 API")]
                currentIndex: root.newsBackend ? (root.newsBackend.getUseCustomApi() ? 1 : 0) : 0
                onCurrentIndexChanged: {
                    if (root.newsBackend)
                        root.newsBackend.setUseCustomApi(currentIndex === 1)
                }
            }
        }

        // 自定义 API 设置
        SettingCard {
            Layout.fillWidth: true
            visible: sourceCombo.currentIndex === 1

            icon.name: "ic_fluent_link_20_regular"
            title: qsTr("自定义 API 地址")
            description: qsTr("输入自定义新闻 API 的 URL（支持 JSON 格式）")

            TextField {
                id: customApiField
                width: 280
                placeholderText: "https://api.example.com/news"
                text: root.newsBackend ? root.newsBackend.getCustomApiUrl() : ""
                onEditingFinished: {
                    if (root.newsBackend)
                        root.newsBackend.setCustomApiUrl(text)
                }
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

        // 自动刷新间隔
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

        // 新闻更新通知
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

        // 立即刷新
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

        // 分隔线
        Rectangle {
            Layout.fillWidth: true
            Layout.topMargin: 4
            Layout.bottomMargin: 4
            height: 1
            color: Colors.proxy.dividerColor || "#20000000"
        }

        // 数据来源信息
        SettingCard {
            Layout.fillWidth: true

            icon.name: "ic_fluent_info_20_regular"
            title: qsTr("数据来源")
            description: qsTr("当前使用的新闻数据源")

            ColumnLayout {
                spacing: 4

                Text {
                    text: root.lastUpdated ? qsTr("最近更新：%1").arg(root.lastUpdated) : qsTr("尚未更新")
                    typography: Typography.Caption
                    color: Colors.proxy.textSecondaryColor
                }

                Text {
                    text: {
                        if (root.newsBackend && root.newsBackend.getUseCustomApi())
                            return qsTr("使用自定义 API")
                        return qsTr("默认：新浪新闻")
                    }
                    typography: Typography.Caption
                    color: Colors.proxy.textSecondaryColor
                }
            }
        }
    }
}
