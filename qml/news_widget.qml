import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RinUI
import ClassWidgets.Theme

Widget {
    id: root

    text: qsTr("今日新闻")

    // 固定组件宽度（不被内容撑变），高度保持与其他组件一致的标准高度
    implicitWidth: 380

    // 内容可视宽度 = 组件宽度 - 左右内边距（mini 16×2，普通 24×2）
    property real contentWidth: root.width - (root.miniMode ? 16 : 24) * 2

    implicitHeight: miniMode ? 32 : ((settings && settings.widget_height !== undefined) ? settings.widget_height : 280)
    cornerRadius: 16

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
    readonly property color cardBgColor: isDark ? "#1AFFFFFF" : "#08000000"

    readonly property int maxItems: (settings && settings.max_items !== undefined) ? settings.max_items : 8
    readonly property bool showScore: settings ? (settings.show_score !== false) : true
    readonly property int itemHeight: (settings && settings.item_height !== undefined) ? settings.item_height : 38

    readonly property var newsDataList: (newsData && newsData.news) ? newsData.news : []

    readonly property string miniTitle: {
        let parts = []
        for (let i = 0; i < Math.min(newsDataList.length, 5); i++)
            parts.push(newsDataList[i].title)
        if (parts.length === 0) return qsTr("今日新闻 · 暂无数据")
        return parts.join("    |    ")
    }

    readonly property string statusText: {
        if (!newsData || newsData.updated === "") return qsTr("尚未获取新闻")
        if (status === "loading") return qsTr("更新中…")
        if (status === "error") return qsTr("更新失败")
        return (newsData.source ? newsData.source + " · " : "") + qsTr("更新于 ") + newsData.updated
    }

    function applyData(d) {
        if (!d) return
        newsData = d
        status = "ready"
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

    // 迷你模式 - 新闻滚动条
    Item {
        visible: miniMode
        anchors.fill: parent
        anchors.margins: 8
        clip: true

        Row {
            id: scrollingRow
            anchors.verticalCenter: parent.verticalCenter
            spacing: 40

            // 第一条新闻文本
            Text {
                id: scrollingText1
                text: root.miniTitle
                font.pixelSize: 12
                color: root.textColor
                anchors.verticalCenter: parent.verticalCenter
                width: implicitWidth
            }

            // 第二条新闻文本（用于无缝滚动）
            Text {
                id: scrollingText2
                text: root.miniTitle
                font.pixelSize: 12
                color: root.textColor
                anchors.verticalCenter: parent.verticalCenter
                width: implicitWidth
            }
        }

        // 滚动动画
        NumberAnimation {
            id: scrollAnimation
            target: scrollingRow
            property: "x"
            from: root.width
            to: -scrollingText1.implicitWidth - 40
            duration: Math.max(scrollingText1.implicitWidth * 20, 15000)
            loops: Animation.Infinite
            running: miniMode && root.newsDataList.length > 0
        }

        // 当内容超出可视区域时启动滚动
        onWidthChanged: {
            if (width > 0 && scrollingText1.implicitWidth > width) {
                scrollAnimation.start()
            } else {
                scrollAnimation.stop()
                scrollingRow.x = 0
            }
        }
    }

    // 常规模式
    ColumnLayout {
        visible: !miniMode
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        // 标题栏
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                text: qsTr("今日新闻")
                font.pixelSize: 15
                font.bold: true
                color: root.textColor
            }

            Item { Layout.fillWidth: true }

            Rectangle {
                visible: root.status === "loading"
                width: 16
                height: 16
                radius: 8
                color: "transparent"
                border.width: 2
                border.color: root.accentColor

                RotationAnimation on rotation {
                    from: 0
                    to: 360
                    duration: 1000
                    loops: Animation.Infinite
                    running: root.status === "loading"
                }
            }

            Text {
                text: root.statusText
                font.pixelSize: 11
                color: root.subTextColor
            }
        }

        // 新闻列表
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                id: newsListView
                anchors.fill: parent
                clip: true
                spacing: 4
                model: root.newsDataList.slice(0, root.maxItems)
                delegate: newsDelegate
                boundsBehavior: Flickable.StopAtBounds

                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AsNeeded
                }
            }

            // 空状态
            Item {
                anchors.fill: parent
                visible: root.newsDataList.length === 0

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 12

                    Icon {
                        Layout.alignment: Qt.AlignHCenter
                        name: root.status === "loading" ? "ic_fluent_arrow_sync_20_regular" : "ic_fluent_news_20_regular"
                        size: 32
                        color: root.subTextColor
                        opacity: 0.5

                        RotationAnimation on rotation {
                            from: 0
                            to: 360
                            duration: 1000
                            loops: Animation.Infinite
                            running: root.status === "loading"
                        }
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: {
                            if (root.status === "loading") return qsTr("正在加载新闻…")
                            if (root.status === "error") return qsTr("加载失败，请检查网络")
                            return qsTr("暂无新闻")
                        }
                        font.pixelSize: 13
                        color: root.subTextColor
                    }

                    Button {
                        Layout.alignment: Qt.AlignHCenter
                        visible: root.status === "error" || (root.status === "ready" && root.newsDataList.length === 0)
                        text: qsTr("刷新")
                        icon.name: "ic_fluent_arrow_sync_20_regular"
                        onClicked: { if (backend) backend.refreshNow() }
                    }
                }
            }
        }

        // 底部工具栏
        RowLayout {
            Layout.fillWidth: true
            spacing: 4

            Text {
                Layout.fillWidth: true
                text: root.newsData.date ? qsTr("%1 · %2 条新闻").arg(root.newsData.date).arg(root.newsDataList.length) : ""
                font.pixelSize: 10
                color: root.subTextColor
                elide: Text.ElideRight
            }

            ToolButton {
                flat: true
                Layout.preferredWidth: 20
                Layout.preferredHeight: 20
                icon.name: "ic_fluent_arrow_sync_20_regular"
                icon.width: 14
                icon.height: 14
                opacity: hovered ? 1.0 : 0.7
                onClicked: { if (backend) backend.refreshNow() }
            }
        }
    }

    Component {
        id: newsDelegate
        Item {
            id: itemRoot
            width: ListView.view ? ListView.view.width : 200
            height: root.itemHeight

            Rectangle {
                anchors.fill: parent
                anchors.leftMargin: 2
                anchors.rightMargin: 2
                radius: 8
                color: itemHover.hovered ? root.hoverColor : root.cardBgColor

                Behavior on color {
                    ColorAnimation { duration: 150 }
                }
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 8

                // 序号
                Rectangle {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    radius: 6
                    color: index < 3 ? root.accentColor : root.fillColor
                    opacity: index < 3 ? 1.0 : 0.8

                    Text {
                        anchors.centerIn: parent
                        text: index + 1
                        font.pixelSize: 11
                        font.bold: index < 3
                        color: index < 3 ? "#FFFFFF" : root.subTextColor
                    }
                }

                // 标题
                Text {
                    Layout.fillWidth: true
                    text: modelData.title || ""
                    font.pixelSize: 13
                    color: root.textColor
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }

                // 热度标记
                Rectangle {
                    visible: root.showScore && modelData.score >= 80
                    implicitWidth: hotText.implicitWidth + 8
                    implicitHeight: 16
                    radius: 4
                    color: root.isDark ? "#33FF7E79" : "#33E81123"
                    Text {
                        id: hotText
                        anchors.centerIn: parent
                        text: qsTr("热")
                        font.pixelSize: 9
                        color: root.isDark ? "#FF7E79" : "#E81123"
                    }
                }

                Rectangle {
                    visible: root.showScore && modelData.score >= 60 && modelData.score < 80
                    implicitWidth: recommendText.implicitWidth + 8
                    implicitHeight: 16
                    radius: 4
                    color: root.isDark ? "#33FFB900" : "#33FF8C00"
                    Text {
                        id: recommendText
                        anchors.centerIn: parent
                        text: qsTr("荐")
                        font.pixelSize: 9
                        color: root.isDark ? "#FFB900" : "#FF8C00"
                    }
                }

                // 链接图标
                Icon {
                    name: "ic_fluent_open_20_regular"
                    size: 12
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
