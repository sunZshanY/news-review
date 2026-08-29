import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RinUI
import ClassWidgets.Theme

Widget {
    id: root

    text: qsTr("今日新闻")

    property real contentWidth: root.width - (root.miniMode ? 16 : 24) * 2

    property int configWidth: (backend && backend.getWidgetWidth) ? backend.getWidgetWidth() : 320
    property int configHeight: (backend && backend.getWidgetHeight) ? backend.getWidgetHeight() : 280
    property int configItemHeight: (backend && backend.getItemHeight) ? backend.getItemHeight() : 38

    implicitWidth: configWidth
    implicitHeight: miniMode ? 56 : configHeight
    height: miniMode ? 56 : configHeight
    cornerRadius: 16

    property var newsData: ({ date: "", updated: "", source: "", news: [] })
    property string status: "idle"
    property int _lastNewsCount: 0
    property string _lastUpdated: ""

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
    readonly property int itemHeight: configItemHeight

    readonly property var newsDataList: newsData && Array.isArray(newsData.news) ? newsData.news : []

    readonly property string miniTitle: {
        let parts = []
        for (let i = 0; i < Math.min(newsDataList.length, 5); i++)
            parts.push(newsDataList[i].title)
        if (parts.length === 0) return qsTr("今日新闻 · 暂无数据")
        return parts.join("    |    ")
    }

    function refreshNews() {
        if (backend && backend.refreshNow) {
            status = "loading"
            backend.refreshNow()
        } else {
            status = "error"
        }
    }

    Timer {
        id: refreshTimer
        interval: 30 * 60 * 1000
        repeat: true
        running: true
        onTriggered: root.refreshNews()
    }

    function pullData() {
        if (!backend) return
        try {
            if (backend.getNewsJson) {
                let jsonStr = backend.getNewsJson()
                if (jsonStr && jsonStr !== "[]") {
                    let nl = JSON.parse(jsonStr)
                    if (nl && nl.length > 0) {
                        let newUpdated = backend.getUpdated ? backend.getUpdated() : ""
                        if (newUpdated !== root._lastUpdated) {
                            root.newsData = {
                                date: backend.getDate ? backend.getDate() : "",
                                updated: newUpdated,
                                source: backend.getSource ? backend.getSource() : "",
                                news: nl
                            }
                            root._lastUpdated = newUpdated
                            root._lastNewsCount = nl.length
                            root.status = "ready"
                            Qt.callLater(tickerArea.restartScroll)
                        }
                    }
                }
            }
        } catch (e) {}
        if (backend.getStatus) {
            let st = backend.getStatus()
            if (st === "error" && root.status !== "ready") root.status = st
            if (st === "loading") root.status = "loading"
        }
    }

    property bool _signalConnected: false

    function tryConnectSignals() {
        if (!backend || _signalConnected) return
        try {
            backend.dataChanged.connect(root._onDataChanged)
            backend.statusChanged.connect(root._onStatusChanged)
            _signalConnected = true
        } catch (e) {}
    }

    function _onDataChanged(d) {
        pullData()
    }

    function _onStatusChanged(st) {
        if (root.status !== "ready" || st === "ready") root.status = st
    }

    Component.onCompleted: {
        pollTimer.start()
    }

    onBackendChanged: {
        tryConnectSignals()
        pullData()
    }

    Timer {
        id: pollTimer
        interval: 1000
        repeat: true
        running: false
        property int attempts: 0
        onTriggered: {
            attempts++
            if (!backend) return
            tryConnectSignals()
            pullData()
            if (root.newsDataList.length > 0 || root.status === "error") {
                interval = 30000
            }
        }
    }

    Item {
        visible: miniMode
        anchors.fill: parent
        anchors.margins: 8
        clip: true

        Row {
            id: scrollingRow
            anchors.verticalCenter: parent.verticalCenter
            spacing: 40

            Text {
                id: scrollingText1
                text: root.miniTitle
                font.pixelSize: 12
                color: root.textColor
                anchors.verticalCenter: parent.verticalCenter
                width: implicitWidth
            }

            Text {
                id: scrollingText2
                text: root.miniTitle
                font.pixelSize: 12
                color: root.textColor
                anchors.verticalCenter: parent.verticalCenter
                width: implicitWidth
            }
        }

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

        onWidthChanged: {
            if (width > 0 && scrollingText1.implicitWidth > width) {
                scrollAnimation.start()
            } else {
                scrollAnimation.stop()
                scrollingRow.x = 0
            }
        }
    }

    ColumnLayout {
        visible: !miniMode
        anchors.fill: parent
        anchors.margins: 12
        spacing: 0

        Item {
            id: tickerArea
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ListView {
                id: newsList
                anchors.fill: parent
                clip: true
                spacing: 4
                model: root.newsDataList.slice(0, root.maxItems)
                boundsBehavior: Flickable.StopAtBounds
                interactive: false
                highlightFollowsCurrentItem: false

                delegate: Item {
                    width: newsList.width
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

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Text {
                                Layout.fillWidth: true
                                text: modelData.title || ""
                                font.pixelSize: 13
                                color: root.textColor
                                elide: Text.ElideRight
                                maximumLineCount: 1
                            }

                            Text {
                                Layout.fillWidth: true
                                visible: modelData.media_name && modelData.media_name !== ""
                                text: modelData.media_name || ""
                                font.pixelSize: 10
                                color: root.subTextColor
                                elide: Text.ElideRight
                                maximumLineCount: 1
                            }
                        }

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

            SequentialAnimation {
                id: scrollAnim
                running: newsList.count > 0 && root.status === "ready"
                        && newsList.contentHeight > newsList.height
                loops: Animation.Infinite

                NumberAnimation {
                    target: newsList
                    property: "contentY"
                    from: 0
                    to: Math.max(0, newsList.contentHeight - newsList.height)
                    duration: Math.max(1, newsList.count - Math.floor(newsList.height / root.itemHeight)) * 3000
                    easing.type: Easing.InOutQuad
                }

                PauseAnimation { duration: 4000 }

                NumberAnimation {
                    target: newsList
                    property: "contentY"
                    to: 0
                    duration: 800
                    easing.type: Easing.InOutQuad
                }

                PauseAnimation { duration: 2000 }
            }

            function restartScroll() {
                newsList.contentY = 0
                scrollAnim.restart()
            }

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
                        onClicked: { root.refreshNews() }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 4
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
                onClicked: { root.refreshNews() }
            }
        }
    }
}
