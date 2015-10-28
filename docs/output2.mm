<map version="freeplane 1.3.0" VERSION="freeplane 1.3.0">
<!--To view this file, download free mind mapping software Freeplane from http://freeplane.sourceforge.net -->
<node TEXT="Root Node" ID="ID_1723255651" CREATED="1283093380553" MODIFIED="1422120995666"><hook NAME="MapStyle">
    <properties SHOW_ICON_FOR_ATTRIBUTES="true" show_icon_for_attributes="true"/>

<map_styles>
<stylenode LOCALIZED_TEXT="styles.root_node">
<stylenode LOCALIZED_TEXT="styles.predefined" POSITION="right">
<stylenode LOCALIZED_TEXT="default" COLOR="#000000" STYLE="as_parent" MAX_WIDTH="600">
<font NAME="SansSerif" SIZE="10" BOLD="false" ITALIC="false"/>
</stylenode>
<stylenode LOCALIZED_TEXT="defaultstyle.details"/>
<stylenode LOCALIZED_TEXT="defaultstyle.note"/>
<stylenode LOCALIZED_TEXT="defaultstyle.floating">
<edge STYLE="hide_edge"/>
<cloud COLOR="#f0f0f0" SHAPE="ROUND_RECT"/>
</stylenode>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.user-defined" POSITION="right">
<stylenode LOCALIZED_TEXT="styles.topic" COLOR="#18898b" STYLE="fork">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.subtopic" COLOR="#cc3300" STYLE="fork">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.subsubtopic" COLOR="#669900">
<font NAME="Liberation Sans" SIZE="10" BOLD="true"/>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.important">
<icon BUILTIN="yes"/>
</stylenode>
</stylenode>
<stylenode LOCALIZED_TEXT="styles.AutomaticLayout" POSITION="right">
<stylenode LOCALIZED_TEXT="AutomaticLayout.level.root" COLOR="#000000">
<font SIZE="18"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,1" COLOR="#0033ff">
<font SIZE="16"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,2" COLOR="#00b439">
<font SIZE="14"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,3" COLOR="#990000">
<font SIZE="12"/>
</stylenode>
<stylenode LOCALIZED_TEXT="AutomaticLayout.level,4" COLOR="#111111">
<font SIZE="10"/>
</stylenode>
</stylenode>
</stylenode>
</map_styles>
</hook>
<hook NAME="AutomaticEdgeColor" COUNTER="0"/>
<node TEXT="Child Node 1" POSITION="right" ID="ID_1707799934" CREATED="1421458652275" MODIFIED="1421458658295">
<node TEXT="Subchild 1 w/ arc cloud" ID="ID_1244434831" CREATED="1421458663887" MODIFIED="1421461041155">
<cloud COLOR="#3333ff" SHAPE="ARC"/>
<node TEXT="sub-subchild w/ star cloud" ID="ID_1458322322" CREATED="1421458700021" MODIFIED="1421461002737">
<cloud COLOR="#cc00cc" SHAPE="STAR"/>
</node>
<node TEXT="subsub w/ rect cloud" ID="ID_404658972" CREATED="1421460955591" MODIFIED="1421460978871">
<cloud COLOR="#ff3333" SHAPE="RECT"/>
</node>
<node TEXT="subsub w/ round rect cloud" ID="ID_1441499441" CREATED="1421461004484" MODIFIED="1421461027812">
<cloud COLOR="#66ff66" SHAPE="ROUND_RECT"/>
</node>
</node>
</node>
<node TEXT="Child Node 2" POSITION="right" ID="ID_612656001" CREATED="1421460933821" MODIFIED="1421460938941">
<edge COLOR="#7c007c"/>
</node>
<node TEXT="Child Node 3 w/ colored edge and thick line and horizontal style" POSITION="right" ID="ID_721787619" CREATED="1421461049972" MODIFIED="1421461123315">
<edge STYLE="horizontal" COLOR="#3333ff" WIDTH="4"/>
</node>
<node TEXT="" POSITION="right" ID="ID_233410359" CREATED="1422119552579" MODIFIED="1422127750193">
<edge COLOR="#ff0000"/>
<attribute NAME="blank text" VALUE="this has blank text"/>
</node>
</node>
</map>
