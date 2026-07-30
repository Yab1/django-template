#!/usr/bin/env python3
# ruff: noqa: E501, E402
"""
Creates, deploys, and starts the "Triage Vitals → EHR" channel in Mirth Connect
via the Mirth REST API — no desktop Administrator app needed.

Usage:
    python create_mirth_channel.py --ehr-token <EHR_JWT_TOKEN>

Options:
    --mirth-host    Mirth host (default: localhost)
    --mirth-port    Mirth HTTPS port (default: 8445)
    --mirth-user    Mirth admin username (default: admin)
    --mirth-pass    Mirth admin password (default: admin)
    --ehr-token     EHR backend JWT access token (required)
    --ehr-url       EHR observation create URL (default: http://172.21.0.1:7000/api/v1/observations/create/)
    --hl7-port      HL7 MLLP listener port inside Mirth container (default: 6661)
"""

import argparse
import ssl
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

TRANSFORMER_JS = (Path(__file__).parent / "mirth_channel_transformer.js").read_text()


def build_channel_xml(channel_id: str, ehr_token: str, ehr_url: str, hl7_port: int) -> str:
    # Escape JS for XML embedding
    js_escaped = TRANSFORMER_JS.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<channel version="4.5.2">
  <id>{channel_id}</id>
  <nextMetaDataId>2</nextMetaDataId>
  <name>Triage Vitals to EHR</name>
  <revision>1</revision>
  <description>WF-03 triage assessment — device vitals via MLLP to EHR observation API</description>
  <enabled>true</enabled>
  <preprocessingScript>return message;</preprocessingScript>
  <postprocessingScript>return;</postprocessingScript>
  <deployScript>return;</deployScript>
  <undeployScript>return;</undeployScript>
  <properties class="channel" version="4.5.2">
    <clearGlobalChannelMap>true</clearGlobalChannelMap>
    <messageStorageMode>DEVELOPMENT</messageStorageMode>
    <encryptData>false</encryptData>
    <removeContentOnCompletion>false</removeContentOnCompletion>
    <removeOnlyFilteredOnCompletion>false</removeOnlyFilteredOnCompletion>
    <removeAttachmentsOnCompletion>false</removeAttachmentsOnCompletion>
    <initialState>STARTED</initialState>
    <storeAttachments>false</storeAttachments>
    <tags class="linked-hash-set"/>
    <metaDataColumns/>
    <attachmentProperties version="4.5.2">
      <type>None</type>
    </attachmentProperties>
    <resourceIds class="linked-hash-map">
      <entry>
        <string>Default Resource</string>
        <string>[Default Resource]</string>
      </entry>
    </resourceIds>
  </properties>
  <sourceConnector version="4.5.2">
    <metaDataId>0</metaDataId>
    <name>sourceConnector</name>
    <properties class="com.mirth.connect.connectors.tcp.TcpReceiverProperties" version="4.5.2">
      <pluginProperties/>
      <listenerConnectorProperties version="4.5.2">
        <host>0.0.0.0</host>
        <port>{hl7_port}</port>
      </listenerConnectorProperties>
      <sourceConnectorProperties version="4.5.2">
        <responseVariable>None</responseVariable>
        <respondAfterProcessing>true</respondAfterProcessing>
        <processBatch>false</processBatch>
        <firstResponse>false</firstResponse>
        <processingThreads>1</processingThreads>
        <resourceIds class="linked-hash-map">
          <entry>
            <string>Default Resource</string>
            <string>[Default Resource]</string>
          </entry>
        </resourceIds>
        <queueBufferSize>1000</queueBufferSize>
      </sourceConnectorProperties>
      <transmissionModeProperties class="com.mirth.connect.model.transmission.framemode.FrameModeProperties" version="4.5.2">
        <pluginPointName>MLLP</pluginPointName>
        <startOfMessageBytes>0B</startOfMessageBytes>
        <endOfMessageBytes>1C0D</endOfMessageBytes>
      </transmissionModeProperties>
      <serverMode>true</serverMode>
      <remoteAddress/>
      <remotePort/>
      <overrideLocalBinding>false</overrideLocalBinding>
      <reconnectInterval>5000</reconnectInterval>
      <receiveTimeout>0</receiveTimeout>
      <bufferSize>65536</bufferSize>
      <maxConnections>10</maxConnections>
      <keepConnectionOpen>true</keepConnectionOpen>
      <dataTypeBinary>false</dataTypeBinary>
      <charsetEncoding>DEFAULT_ENCODING</charsetEncoding>
      <respondOnNewConnection>0</respondOnNewConnection>
      <responseAddress/>
      <responsePort/>
    </properties>
    <transformer version="4.5.2">
      <elements>
        <com.mirth.connect.plugins.javascriptstep.JavaScriptStep version="4.5.2">
          <name>Map HL7 to EHR JSON</name>
          <sequenceNumber>0</sequenceNumber>
          <enabled>true</enabled>
          <script>{js_escaped}</script>
        </com.mirth.connect.plugins.javascriptstep.JavaScriptStep>
      </elements>
      <inboundTemplate/>
      <outboundTemplate/>
      <inboundDataType>HL7V2</inboundDataType>
      <outboundDataType>RAW</outboundDataType>
      <inboundProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2DataTypeProperties" version="4.5.2">
        <serializationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2SerializationProperties" version="4.5.2">
          <handleRepetitions>true</handleRepetitions>
          <handleSubcomponents>true</handleSubcomponents>
          <useStrictParser>false</useStrictParser>
          <useStrictValidation>false</useStrictValidation>
          <stripNamespaces>true</stripNamespaces>
          <segmentDelimiter>\\r</segmentDelimiter>
          <convertLineBreaks>true</convertLineBreaks>
        </serializationProperties>
        <deserializationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2DeserializationProperties" version="4.5.2">
          <useStrictParser>false</useStrictParser>
          <useStrictValidation>false</useStrictValidation>
          <segmentDelimiter>\\r</segmentDelimiter>
        </deserializationProperties>
        <batchProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2BatchProperties" version="4.5.2">
          <splitType>MSH_Segment</splitType>
          <batchScript/>
        </batchProperties>
        <responseGenerationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2ResponseGenerationProperties" version="4.5.2">
          <segmentDelimiter>\\r</segmentDelimiter>
          <successfulACKCode>AA</successfulACKCode>
          <successfulACKMessage/>
          <errorACKCode>AE</errorACKCode>
          <errorACKMessage>An error occurred processing the message.</errorACKMessage>
          <rejectedACKCode>AR</rejectedACKCode>
          <rejectedACKMessage>The message was rejected.</rejectedACKMessage>
          <msh15ACKAccept>false</msh15ACKAccept>
          <dateFormat>yyyyMMddHHmmss</dateFormat>
        </responseGenerationProperties>
        <responseValidationProperties class="com.mirth.connect.plugins.datatypes.hl7v2.HL7v2ResponseValidationProperties" version="4.5.2">
          <successfulACKCode>AA,CA</successfulACKCode>
          <errorACKCode>AE,CE</errorACKCode>
          <rejectedACKCode>AR,CR</rejectedACKCode>
          <validateMessageControlId>true</validateMessageControlId>
          <originalMessageControlId>Destination_Encoded</originalMessageControlId>
          <originalIdMapVariable/>
        </responseValidationProperties>
      </inboundProperties>
      <outboundProperties class="com.mirth.connect.plugins.datatypes.raw.RawDataTypeProperties" version="4.5.2">
        <serializationProperties class="com.mirth.connect.plugins.datatypes.raw.RawSerializationProperties" version="4.5.2">
          <charsetEncoding>DEFAULT_ENCODING</charsetEncoding>
          <binary>false</binary>
        </serializationProperties>
      </outboundProperties>
    </transformer>
    <filter version="4.5.2">
      <elements/>
    </filter>
    <transportName>TCP Listener</transportName>
    <mode>SOURCE</mode>
    <enabled>true</enabled>
    <waitForPrevious>true</waitForPrevious>
  </sourceConnector>
  <destinationConnectors>
    <connector version="4.5.2">
      <metaDataId>1</metaDataId>
      <name>EHR Observation Create</name>
      <properties class="com.mirth.connect.connectors.http.HttpDispatcherProperties" version="4.5.2">
        <pluginProperties/>
        <destinationConnectorProperties version="4.5.2">
          <queueEnabled>false</queueEnabled>
          <sendFirst>false</sendFirst>
          <retryIntervalMillis>10000</retryIntervalMillis>
          <regenerateTemplate>false</regenerateTemplate>
          <retryCount>0</retryCount>
          <rotate>false</rotate>
          <includeFilterTransformer>false</includeFilterTransformer>
          <threadCount>1</threadCount>
          <threadAssignmentVariable/>
          <validateResponse>false</validateResponse>
          <resourceIds class="linked-hash-map">
            <entry>
              <string>Default Resource</string>
              <string>[Default Resource]</string>
            </entry>
          </resourceIds>
          <queueBufferSize>1000</queueBufferSize>
          <reattachAttachments>true</reattachAttachments>
        </destinationConnectorProperties>
        <host>{ehr_url}</host>
        <useProxyServer>false</useProxyServer>
        <proxyAddress/>
        <proxyPort/>
        <method>POST</method>
        <headers class="linked-hash-map">
          <entry>
            <string>Content-Type</string>
            <list>
              <string>application/json</string>
            </list>
          </entry>
          <entry>
            <string>Authorization</string>
            <list>
              <string>Bearer {ehr_token}</string>
            </list>
          </entry>
        </headers>
        <parameters class="linked-hash-map"/>
        <useHeadersVariable>false</useHeadersVariable>
        <headersVariable/>
        <useParametersVariable>false</useParametersVariable>
        <parametersVariable/>
        <responseXmlBody>false</responseXmlBody>
        <responseParseMultipart>true</responseParseMultipart>
        <responseIncludeMetadata>false</responseIncludeMetadata>
        <responseBinaryMimeTypes>application/octet-stream,image/jpeg,image/png</responseBinaryMimeTypes>
        <responseBinaryMimeTypesRegex>false</responseBinaryMimeTypesRegex>
        <multipart>false</multipart>
        <useAuthentication>false</useAuthentication>
        <authenticationType>Basic</authenticationType>
        <usePreemptiveAuthentication>false</usePreemptiveAuthentication>
        <username/>
        <password/>
        <content>${{message.encodedData}}</content>
        <contentType>application/json</contentType>
        <dataTypeBinary>false</dataTypeBinary>
        <charset>UTF-8</charset>
        <socketTimeout>30000</socketTimeout>
      </properties>
      <transformer version="4.5.2">
        <elements/>
        <inboundTemplate/>
        <outboundTemplate/>
        <inboundDataType>RAW</inboundDataType>
        <outboundDataType>RAW</outboundDataType>
        <inboundProperties class="com.mirth.connect.plugins.datatypes.raw.RawDataTypeProperties" version="4.5.2">
          <serializationProperties class="com.mirth.connect.plugins.datatypes.raw.RawSerializationProperties" version="4.5.2">
            <charsetEncoding>DEFAULT_ENCODING</charsetEncoding>
            <binary>false</binary>
          </serializationProperties>
        </inboundProperties>
        <outboundProperties class="com.mirth.connect.plugins.datatypes.raw.RawDataTypeProperties" version="4.5.2">
          <serializationProperties class="com.mirth.connect.plugins.datatypes.raw.RawSerializationProperties" version="4.5.2">
            <charsetEncoding>DEFAULT_ENCODING</charsetEncoding>
            <binary>false</binary>
          </serializationProperties>
        </outboundProperties>
      </transformer>
      <filter version="4.5.2">
        <elements/>
      </filter>
      <transportName>HTTP Sender</transportName>
      <mode>DESTINATION</mode>
      <enabled>true</enabled>
      <waitForPrevious>true</waitForPrevious>
    </connector>
  </destinationConnectors>
</channel>"""


import http.cookiejar
import urllib.parse


class MirthClient:
    def __init__(self, host: str, port: int, verify_ssl: bool = False):
        self.base = f"https://{host}:{port}/api"
        self.ctx = ssl.create_default_context()
        if not verify_ssl:
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE
        # Cookie jar automatically carries JSESSIONID across requests
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=self.ctx),
            urllib.request.HTTPCookieProcessor(self.jar),
        )

    def _request(
        self, method: str, path: str, body: str = None, content_type: str = "application/xml"
    ) -> tuple[int, str]:
        url = f"{self.base}{path}"
        headers = {"Accept": "*/*", "X-Requested-With": "XMLHttpRequest"}
        if body:
            headers["Content-Type"] = content_type
        data = body.encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=15) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

    def login(self, username: str, password: str) -> None:
        body = f"username={urllib.parse.quote(username)}&password={urllib.parse.quote(password)}"
        status, resp_body = self._request("POST", "/users/_login", body, "application/x-www-form-urlencoded")
        if status not in (200, 204):
            sys.exit(1)

    def create_channel(self, xml: str) -> str:
        status, body = self._request("POST", "/channels", xml)
        if status not in (200, 201):
            sys.exit(1)
        return body

    def deploy_channel(self, channel_id: str) -> None:
        # Per-channel deploy — no body required
        status, body = self._request("POST", f"/channels/{channel_id}/_deploy")
        if status not in (200, 204):
            sys.exit(1)

    def start_channel(self, channel_id: str) -> None:
        # Per-channel start — no body required
        status, body = self._request("POST", f"/channels/{channel_id}/_start")
        if status not in (200, 204):
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Triage Vitals channel in Mirth Connect")
    parser.add_argument("--mirth-host", default="localhost")
    parser.add_argument("--mirth-port", type=int, default=8445)
    parser.add_argument("--mirth-user", default="admin")
    parser.add_argument("--mirth-pass", default="admin")
    parser.add_argument("--ehr-token", required=True, help="EHR JWT access token")
    parser.add_argument("--ehr-url", default="http://172.21.0.1:7000/api/v1/observations/create/")
    parser.add_argument("--hl7-port", type=int, default=6661)
    args = parser.parse_args()

    channel_id = str(uuid.uuid4())

    xml = build_channel_xml(
        channel_id=channel_id,
        ehr_token=args.ehr_token,
        ehr_url=args.ehr_url,
        hl7_port=args.hl7_port,
    )

    client = MirthClient(args.mirth_host, args.mirth_port)
    client.login(args.mirth_user, args.mirth_pass)
    client.create_channel(xml)
    client.deploy_channel(channel_id)
    client.start_channel(channel_id)


if __name__ == "__main__":
    main()
