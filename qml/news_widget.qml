import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RinUI
import ClassWidgets.Theme

Widget {
    id: root

    text: qsTr("今日新闻")
    implicitWidth: 200
    height: miniMode ? 32 : 300

    // 由 WidgetLoader 注入：
    // property var backend  （基类已有）
    // property var settings （基类已有）

    property var newsData: ({ date: "", updated: "", source: "", news: [] })
    property string status: "idle"

    readonly property bool isDark: Theme.isDark()
    readonly property color textColor: Colors.proxy.textColor !== undefined
        ? Colors.proxy.textColor : (isDark ? "#F2F2F2" : "#1B1B1B")
    readonly property color subTextColor: Colors.proxy.textSecondaryColor !== undefined
        ? Colors.proxy.textSecondaryColor : (isDark ? "#A6A6A6" : "#6B6B6B")
    readonly property color accentColor: Colors.proxy.primaryColor !== undefined
        ? Colors.proxy.primaryColor : (isDark ? "#7EB6FF" : "#0F6CBD")
    readonly property color fillColor: Colors.proxy.controlFillColor !== undefined
        ? Colors.proxy.controlFillColor : (isDark ? "#24FFFFFF" : "#12000000")
    readonly property color hoverColor: isDark ? "#2EFFFFFF" : "#1A000000"
    readonly property color borderColor: Colors.proxy.controlBorderColor !== undefined
        ? Colors.proxy.controlBorderColor : (isDark ? "#40FFFFFF" : "#26000000")

    readonly property int maxItems: (settings && settings.max_items !== undefined) ? settings.max_items : 8
    readonly property bool showScore: settings ? (settings.show_score !== false) : true

    readonly property var newsList: (newsData && newsData.news) ? newsData.news : []

    readonly property string miniTitle: {
        let parts = []
        for (let i = 0; i < Math.min(newsList.length, 5); i++)
            parts.push(newsList[i].title)
        if (parts.length === 0) return qsTr("今日新闻 · 暂无数据")
        return parts.join("    ")
    }

    readonly property string statusText: {
        if (!newsData || newsData.updated === "") return qsTr("尚未获取新闻")
        if (status === "loading") return qsTr("更新中…")
        if (status === "error") return qsTr("更新失败，请点击右侧按钮重试")
        return (newsData.source ? newsData.source + " · " : "") + qsTr("更新于 ") + newsData.updated
    }

    function applyData(d) {
        if (!d) return
        newsData = d
        status = "ready"
        if (newsList) newsList.positionViewAtBeginning()
    }

    onBackendChanged: {
        if (backend) {
            backendConn.target = backend
            if (backend.getData) applyData(backend.getData())
            if (backend.getStatus) status = backend.getStatus()
        }
    }

    Connections {
        id: backendConn
        function onDataChanged(d) { root.applyData(d) }
        function onStatusChanged(st) { root.status = st }
    }

    // 迷你模式：滚动显示今日头条
    MarqueeTitle {
        visible: miniMode
        anchors.centerIn: parent
        width: 200
        text: root.miniTitle
    }

    // 常规模式
    ColumnLayout {
        visible: !miniMode
        anchors.fill: parent
        spacing: 8

        // 新闻列表
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                id: newsList
                anchors.fill: parent
                clip: true
                spacing: 2
                model: root.newsList.slice(0, root.maxItems)
                ScrollBar.vertical: ScrollBar {}
                delegate: newsDelegate
                boundsBehavior: Flickable.StopAtBounds
                highlightMoveDuration: 200
                highlightRangeMode: ListView.ApplyRange
                preferredHighlightBegin: 0
                preferredHighlightEnd: 0
                
                // 弹回动画效果
                Behavior on contentY {
                    NumberAnimation {
                        duration: 300
                        easing.type: Easing.OutBounce
                        easing.amplitude: 0.5
                    }
                }
            }

            // 空状态 / 错误状态
            Item {
                anchors.fill: parent
                visible: root.newsList.length === 0

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 8

                    BusyIndicator {
                        Layout.alignment: Qt.AlignHCenter
                        running: root.status === "loading"
                        visible: root.status === "loading"
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: {
                            if (root.status === "loading") return qsTr("正在加载新闻…")
                            if (root.status === "error") return qsTr("加载失败，请检查网络连接")
                            return qsTr("暂无新闻")
                        }
                        font.pixelSize: 13
                        color: root.subTextColor
                    }

                    Button {
                        Layout.alignment: Qt.AlignHCenter
                        visible: root.status === "error" || (root.status === "ready" && root.newsList.length === 0)
                        text: qsTr("刷新")
                        onClicked: { if (backend) backend.refreshNow() }
                    }
                }
            }
        }

        // 底部状态栏
        RowLayout {
            Layout.fillWidth: true
            spacing: 4

            Text {
                Layout.fillWidth: true
                text: root.statusText
                font.pixelSize: 11
                color: root.subTextColor
                elide: Text.ElideRight
            }

            ToolButton {
                flat: true
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                icon.name: "ic_fluent_arrow_sync_20_regular"
                opacity: root.status === "loading" ? 0.55 : 0.85
                RotationAnimation on rotation {
                    from: 0
                    to: 360
                    duration: 900
                    loops: Animation.Infinite
                    running: root.status === "loading"
                }
                onClicked: { if (backend) backend.refreshNow() }
            }
        }
    }

    Component {
        id: newsDelegate
        Item {
            id: itemRoot
            width: ListView.view ? ListView.view.width : 200
            height: 36

            Rectangle {
                anchors.fill: parent
                radius: 6
                color: itemHover.hovered ? root.hoverColor : "transparent"
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 8

                Text {
                    Layout.preferredWidth: 20
                    text: index + 1
                    font.pixelSize: 12
                    font.bold: true
                    color: index < 3 ? root.accentColor : root.subTextColor
                    horizontalAlignment: Text.AlignHCenter
                }

                Text {
                    Layout.fillWidth: true
                    text: modelData.title
                    font.pixelSize: 14
                    color: root.textColor
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }

                Rectangle {
                    visible: root.showScore && modelData.score >= 80
                    implicitWidth: hotText.implicitWidth + 10
                    implicitHeight: 16
                    radius: 4
                    color: root.isDark ? "#33FF7E79" : "#33E81123"
                    Text {
                        id: hotText
                        anchors.centerIn: parent
                        text: qsTr("热")
                        font.pixelSize: 10
                        color: root.isDark ? "#FF7E79" : "#E81123"
                    }
                }

                Rectangle {
                    visible: root.showScore && modelData.score >= 60 && modelData.score < 80
                    implicitWidth: recommendText.implicitWidth + 10
                    implicitHeight: 16
                    radius: 4
                    color: root.isDark ? "#33FFB900" : "#33FF8C00"
                    Text {
                        id: recommendText
                        anchors.centerIn: parent
                        text: qsTr("荐")
                        font.pixelSize: 10
                        color: root.isDark ? "#FFB900" : "#FF8C00"
                    }
                }

                Icon {
                    name: "ic_fluent_open_20_regular"
                    size: 13
                    color: root.subTextColor
                    visible: itemHover.hovered && modelData.url !== ""
                }
            }

            HoverHandler { id: itemHover }

            TapHandler {
                onTapped: {
                    if (modelData.url) Qt.openUrlExternally(modelData.url)
                }
            }
        }
    }
}
