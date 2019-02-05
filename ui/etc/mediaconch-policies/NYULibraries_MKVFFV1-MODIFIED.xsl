<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="https://mediaarea.net/mediaconch" xmlns:ma="https://mediaarea.net/mediaarea" xmlns:mi="https://mediaarea.net/mediainfo" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0" extension-element-prefixes="xsi ma">
  <xsl:output encoding="UTF-8" method="xml" version="1.0" indent="yes"/>
  <xsl:template match="ma:MediaArea">
    <MediaConch>
      <xsl:attribute name="version">
        <xsl:text>0.1</xsl:text>
      </xsl:attribute>
      <xsl:for-each select="ma:media">
        <media>
          <xsl:attribute name="ref">
            <xsl:value-of select="./@ref"/>
          </xsl:attribute>
          <policyChecks>
            <name>Preservation Master File Recommendations - Matroska/FFV1 (NYU Libraries)</name>
            <description/>
            <check>
              <xsl:attribute name="name">General Format equals Matroska</xsl:attribute>
              <context>
                <xsl:attribute name="field">Format</xsl:attribute>
                <xsl:attribute name="value">Matroska</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='General'][*]/mi:Format">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='General'][*]/mi:Format">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">Matroska</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Video Format is FFV1</xsl:attribute>
              <context>
                <xsl:attribute name="field">Format</xsl:attribute>
                <xsl:attribute name="value">FFV1</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Video'][*]/mi:Format">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Video'][*]/mi:Format">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">FFV1</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Video CodecID equals FFV1</xsl:attribute>
              <context>
                <xsl:attribute name="field">CodecID</xsl:attribute>
                <xsl:attribute name="value">V_MS/VFW/FOURCC / FFV1</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Video'][*]/mi:CodecID">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Video'][*]/mi:CodecID">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">V_MS/VFW/FOURCC / FFV1</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Video Width equals 720 (pixels)</xsl:attribute>
              <context>
                <xsl:attribute name="field">Width</xsl:attribute>
                <xsl:attribute name="value">720</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Video'][*]/mi:Width">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Video'][*]/mi:Width">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">720</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Video Height equals 486 (pixels)</xsl:attribute>
              <context>
                <xsl:attribute name="field">Height</xsl:attribute>
                <xsl:attribute name="value">486</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Video'][*]/mi:Height">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Video'][*]/mi:Height">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">486</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Video DisplayAspectRatio equals 4:3 (1.333)</xsl:attribute>
              <context>
                <xsl:attribute name="field">DisplayAspectRatio</xsl:attribute>
                <xsl:attribute name="value">1.333</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Video'][*]/mi:DisplayAspectRatio">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Video'][*]/mi:DisplayAspectRatio">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">1.333</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Video FrameRate equals 29.97 fps (29.970)</xsl:attribute>
              <context>
                <xsl:attribute name="field">FrameRate</xsl:attribute>
                <xsl:attribute name="value">29.970</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Video'][*]/mi:FrameRate">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Video'][*]/mi:FrameRate">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">29.970</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Video Standard equals NTSC</xsl:attribute>
              <context>
                <xsl:attribute name="field">Standard</xsl:attribute>
                <xsl:attribute name="value">NTSC</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Video'][*]/mi:Standard">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Video'][*]/mi:Standard">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">NTSC</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Video ColorSpace equals YUV</xsl:attribute>
              <context>
                <xsl:attribute name="field">ColorSpace</xsl:attribute>
                <xsl:attribute name="value">YUV</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Video'][*]/mi:ColorSpace">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Video'][*]/mi:ColorSpace">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">YUV</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Video ChromaSubsampling equals 4:2:0</xsl:attribute>
              <context>
                <xsl:attribute name="field">ChromaSubsampling</xsl:attribute>
                <xsl:attribute name="value">4:2:0</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Video'][*]/mi:ChromaSubsampling">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Video'][*]/mi:ChromaSubsampling">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">4:2:0</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Video BitDepth equals 8 (bits)</xsl:attribute>
              <context>
                <xsl:attribute name="field">BitDepth</xsl:attribute>
                <xsl:attribute name="value">8</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Video'][*]/mi:BitDepth">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Video'][*]/mi:BitDepth">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">8</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Audio Format equals PCM</xsl:attribute>
              <context>
                <xsl:attribute name="field">Format</xsl:attribute>
                <xsl:attribute name="value">PCM</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Audio'][*]/mi:Format">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Audio'][*]/mi:Format">
                    <xsl:call-template name="is_equal">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">PCM</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Audio Channels are greater or equal than 1</xsl:attribute>
              <context>
                <xsl:attribute name="field">Channels</xsl:attribute>
                <xsl:attribute name="value">1</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Audio'][*]/mi:Channels">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Audio'][*]/mi:Channels">
                    <xsl:call-template name="is_greater_or_equal_than">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">1</xsl:with-param>
                      <xsl:with-param name="field">Channels</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Audio SamplingRate is greater or equal than 48 kHz (48000)</xsl:attribute>
              <context>
                <xsl:attribute name="field">SamplingRate</xsl:attribute>
                <xsl:attribute name="value">48000</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Audio'][*]/mi:SamplingRate">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Audio'][*]/mi:SamplingRate">
                    <xsl:call-template name="is_greater_or_equal_than">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">48000</xsl:with-param>
                      <xsl:with-param name="field">SamplingRate</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
            <check>
              <xsl:attribute name="name">Audio BitDepth is greater or equal than 16-bit</xsl:attribute>
              <context>
                <xsl:attribute name="field">BitDepth</xsl:attribute>
                <xsl:attribute name="value">16</xsl:attribute>
              </context>
              <xsl:choose>
                <xsl:when test="mi:MediaInfo/mi:track[@type='Audio'][*]/mi:BitDepth">
                  <xsl:for-each select="mi:MediaInfo/mi:track[@type='Audio'][*]/mi:BitDepth">
                    <xsl:call-template name="is_greater_or_equal_than">
                      <xsl:with-param name="xpath" select="."/>
                      <xsl:with-param name="value">16</xsl:with-param>
                      <xsl:with-param name="field">BitDepth</xsl:with-param>
                    </xsl:call-template>
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>
            </check>
          </policyChecks>
        </media>
      </xsl:for-each>
    </MediaConch>
  </xsl:template>
  <xsl:template name="is_true">
    <xsl:param name="xpath"/>
    <xsl:element name="test">
      <xsl:if test="../@type">
        <xsl:attribute name="tracktype">
          <xsl:value-of select="../@type"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../@typeorder">
        <xsl:attribute name="tracktypeorder">
          <xsl:value-of select="../@typeorder"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../mi:ID">
          <xsl:attribute name="trackid">
              <xsl:value-of select="../mi:ID"/>
          </xsl:attribute>
      </xsl:if>
      <xsl:choose>
        <xsl:when test="$xpath">
          <xsl:attribute name="outcome">pass</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="outcome">fail</xsl:attribute>
          <xsl:attribute name="reason">is not true</xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>
  <xsl:template name="is_equal">
    <xsl:param name="xpath"/>
    <xsl:param name="value"/>
    <xsl:element name="test">
      <xsl:if test="../@type">
        <xsl:attribute name="tracktype">
          <xsl:value-of select="../@type"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../@typeorder">
        <xsl:attribute name="tracktypeorder">
          <xsl:value-of select="../@typeorder"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../mi:ID">
          <xsl:attribute name="trackid">
              <xsl:value-of select="../mi:ID"/>
          </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="actual">
        <xsl:value-of select="$xpath"/>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="$xpath = $value">
          <xsl:attribute name="outcome">pass</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="outcome">fail</xsl:attribute>
          <xsl:attribute name="reason">is not equal</xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>
  <xsl:template name="is_not_equal">
    <xsl:param name="xpath"/>
    <xsl:param name="value"/>
    <xsl:element name="test">
      <xsl:if test="../@type">
        <xsl:attribute name="tracktype">
          <xsl:value-of select="../@type"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../@typeorder">
        <xsl:attribute name="tracktypeorder">
          <xsl:value-of select="../@typeorder"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../mi:ID">
          <xsl:attribute name="trackid">
              <xsl:value-of select="../mi:ID"/>
          </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="actual">
        <xsl:value-of select="$xpath"/>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="$xpath != $value">
          <xsl:attribute name="outcome">pass</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="outcome">fail</xsl:attribute>
          <xsl:attribute name="reason">is equal</xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>
  <xsl:template name="is_greater_than">
    <xsl:param name="xpath"/>
    <xsl:param name="value"/>
    <xsl:element name="test">
      <xsl:if test="../@type">
        <xsl:attribute name="tracktype">
          <xsl:value-of select="../@type"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../@typeorder">
        <xsl:attribute name="tracktypeorder">
          <xsl:value-of select="../@typeorder"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../mi:ID">
          <xsl:attribute name="trackid">
              <xsl:value-of select="../mi:ID"/>
          </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="actual">
        <xsl:value-of select="$xpath"/>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="$xpath &gt; $value">
          <xsl:attribute name="outcome">pass</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="outcome">fail</xsl:attribute>
          <xsl:attribute name="reason">is less than or equal</xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>
  <xsl:template name="is_less_than">
    <xsl:param name="xpath"/>
    <xsl:param name="value"/>
    <xsl:element name="test">
      <xsl:if test="../@type">
        <xsl:attribute name="tracktype">
          <xsl:value-of select="../@type"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../@typeorder">
        <xsl:attribute name="tracktypeorder">
          <xsl:value-of select="../@typeorder"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../mi:ID">
          <xsl:attribute name="trackid">
              <xsl:value-of select="../mi:ID"/>
          </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="actual">
        <xsl:value-of select="$xpath"/>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="$xpath &lt; $value">
          <xsl:attribute name="outcome">pass</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="outcome">fail</xsl:attribute>
          <xsl:attribute name="reason">is greater than or equal</xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>
  <xsl:template name="is_greater_or_equal_than">
    <xsl:param name="xpath"/>
    <xsl:param name="value"/>
    <xsl:element name="test">
      <xsl:if test="../@type">
        <xsl:attribute name="tracktype">
          <xsl:value-of select="../@type"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../@typeorder">
        <xsl:attribute name="tracktypeorder">
          <xsl:value-of select="../@typeorder"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../mi:ID">
          <xsl:attribute name="trackid">
              <xsl:value-of select="../mi:ID"/>
          </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="actual">
        <xsl:value-of select="$xpath"/>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="$xpath &gt;= $value">
          <xsl:attribute name="outcome">pass</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="outcome">fail</xsl:attribute>
          <xsl:attribute name="reason">is less than</xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>
  <xsl:template name="is_less_or_equal_than">
    <xsl:param name="xpath"/>
    <xsl:param name="value"/>
    <xsl:element name="test">
      <xsl:if test="../@type">
        <xsl:attribute name="tracktype">
          <xsl:value-of select="../@type"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../@typeorder">
        <xsl:attribute name="tracktypeorder">
          <xsl:value-of select="../@typeorder"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../mi:ID">
          <xsl:attribute name="trackid">
              <xsl:value-of select="../mi:ID"/>
          </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="actual">
        <xsl:value-of select="$xpath"/>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="$xpath &lt;= $value">
          <xsl:attribute name="outcome">pass</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="outcome">fail</xsl:attribute>
          <xsl:attribute name="reason">is greater than</xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>
  <xsl:template name="exists">
    <xsl:param name="xpath"/>
    <xsl:element name="test">
      <xsl:if test="../@type">
        <xsl:attribute name="tracktype">
          <xsl:value-of select="../@type"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../@typeorder">
        <xsl:attribute name="tracktypeorder">
          <xsl:value-of select="../@typeorder"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../mi:ID">
          <xsl:attribute name="trackid">
              <xsl:value-of select="../mi:ID"/>
          </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="actual">
        <xsl:value-of select="$xpath"/>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="string-length($xpath) != 0">
          <xsl:attribute name="outcome">pass</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="outcome">fail</xsl:attribute>
          <xsl:attribute name="reason">does not exist</xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>
  <xsl:template name="does_not_exist">
    <xsl:param name="xpath"/>
    <xsl:element name="test">
      <xsl:if test="../@type">
        <xsl:attribute name="tracktype">
          <xsl:value-of select="../@type"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../@typeorder">
        <xsl:attribute name="tracktypeorder">
          <xsl:value-of select="../@typeorder"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../mi:ID">
          <xsl:attribute name="trackid">
              <xsl:value-of select="../mi:ID"/>
          </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="actual">
        <xsl:value-of select="$xpath"/>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="string-length($xpath) = '0'">
          <xsl:attribute name="outcome">pass</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="outcome">fail</xsl:attribute>
          <xsl:attribute name="reason">exists</xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>
  <xsl:template name="contains_string">
    <xsl:param name="xpath"/>
    <xsl:param name="value"/>
    <xsl:element name="test">
      <xsl:if test="../@type">
        <xsl:attribute name="tracktype">
          <xsl:value-of select="../@type"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../@typeorder">
        <xsl:attribute name="tracktypeorder">
          <xsl:value-of select="../@typeorder"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="../mi:ID">
          <xsl:attribute name="trackid">
              <xsl:value-of select="../mi:ID"/>
          </xsl:attribute>
      </xsl:if>
      <xsl:attribute name="actual">
        <xsl:value-of select="$xpath"/>
      </xsl:attribute>
      <xsl:choose>
        <xsl:when test="contains($xpath, $value)">
          <xsl:attribute name="outcome">pass</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="outcome">fail</xsl:attribute>
          <xsl:attribute name="reason">does not contain</xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>
</xsl:stylesheet>

