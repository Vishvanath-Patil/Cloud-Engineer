{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": {
          "type": "datasource",
          "uid": "grafana"
        },
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": 75,
  "links": [
    {
      "icon": "bolt",
      "tags": [],
      "targetBlank": true,
      "title": "Update",
      "tooltip": "Update dashboard",
      "type": "link",
      "url": "https://grafana.com/grafana/dashboards/11074"
    },
    {
      "icon": "question",
      "tags": [],
      "targetBlank": true,
      "title": "GitHub",
      "tooltip": "more dashboard",
      "type": "link",
      "url": "https://github.com/starsliao"
    },
    {
      "asDropdown": true,
      "icon": "external link",
      "tags": [],
      "targetBlank": true,
      "title": "",
      "type": "dashboards"
    }
  ],
  "panels": [
    {
      "datasource": {
        "type": "prometheus",
        "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "MB/s",
            "axisPlacement": "left",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              },
              {
                "color": "red",
                "value": 40
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byType",
              "options": "number"
            },
            "properties": [
              {
                "id": "unit",
                "value": "bytes"
              }
            ]
          },
          {
            "matcher": {
              "id": "byType",
              "options": "number"
            },
            "properties": [
              {
                "id": "decimals"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 198,
      "options": {
        "barRadius": 0,
        "barWidth": 1,
        "fullHighlight": false,
        "groupWidth": 0.96,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "always",
        "stacking": "none",
        "tooltip": {
          "hideZeros": false,
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 300
      },
      "pluginVersion": "12.2.0",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "exemplar": false,
          "expr": "topk(10, process_io_write_bytes_per_second{instance=~\"$instance\", process=~\"$process\"})",
          "format": "time_series",
          "instant": true,
          "interval": "",
          "legendFormat": "{{process}}",
          "range": false,
          "refId": "A"
        },
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "expr": "",
          "hide": false,
          "instant": false,
          "legendFormat": "__auto",
          "range": true,
          "refId": "B"
        }
      ],
      "title": "Top Write I/O processes (MB/s)",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "MB/s",
            "axisPlacement": "left",
            "fillOpacity": 80,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 1,
            "scaleDistribution": {
              "type": "linear"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              },
              {
                "color": "red",
                "value": 40
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byType",
              "options": "number"
            },
            "properties": [
              {
                "id": "unit",
                "value": "bytes"
              },
              {
                "id": "decimals"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "id": 199,
      "options": {
        "barRadius": 0,
        "barWidth": 1,
        "fullHighlight": false,
        "groupWidth": 0.96,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "always",
        "stacking": "none",
        "tooltip": {
          "hideZeros": false,
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 300
      },
      "pluginVersion": "12.2.0",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "expr": "topk(10, process_io_read_bytes_per_second{instance=~\"$instance\", process=~\"$process\"})",
          "format": "time_series",
          "instant": true,
          "interval": "",
          "legendFormat": "{{process}}",
          "range": false,
          "refId": "A"
        },
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "expr": "",
          "hide": false,
          "instant": false,
          "legendFormat": "__auto",
          "range": true,
          "refId": "B"
        }
      ],
      "title": "Top Read I/O processes (MB/s)",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "axisSoftMax": 1,
            "axisSoftMin": 0,
            "barAlignment": -1,
            "barWidthFactor": 0.6,
            "drawStyle": "line",
            "fillOpacity": 0,
            "gradientMode": "opacity",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "insertNulls": false,
            "lineInterpolation": "stepAfter",
            "lineStyle": {
              "fill": "solid"
            },
            "lineWidth": 0,
            "pointSize": 2,
            "scaleDistribution": {
              "log": 10,
              "type": "symlog"
            },
            "showPoints": "always",
            "showValues": false,
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "decimals": 1,
          "mappings": [],
          "max": 1,
          "min": 0,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byType",
              "options": "number"
            },
            "properties": [
              {
                "id": "custom.axisLabel",
                "value": "MB/s"
              },
              {
                "id": "unit",
                "value": "bytes"
              },
              {
                "id": "decimals"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 10,
        "w": 24,
        "x": 0,
        "y": 8
      },
      "id": 201,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "hideZeros": false,
          "mode": "multi",
          "sort": "none"
        }
      },
      "pluginVersion": "12.2.0",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "exemplar": false,
          "expr": "topk(10, process_io_read_bytes_per_second{instance=~\"$instance\", process=~\"$process\"})",
          "format": "time_series",
          "instant": false,
          "interval": "1",
          "legendFormat": "{{process}}",
          "range": true,
          "refId": "A"
        }
      ],
      "title": "Per-Process Read I/O (Time Series)",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "axisSoftMax": 1,
            "axisSoftMin": 0,
            "barAlignment": -1,
            "barWidthFactor": 0.6,
            "drawStyle": "line",
            "fillOpacity": 0,
            "gradientMode": "opacity",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "insertNulls": false,
            "lineInterpolation": "stepAfter",
            "lineStyle": {
              "fill": "solid"
            },
            "lineWidth": 0,
            "pointSize": 2,
            "scaleDistribution": {
              "log": 10,
              "type": "symlog"
            },
            "showPoints": "always",
            "showValues": false,
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "decimals": 1,
          "mappings": [],
          "max": 1,
          "min": 0,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byType",
              "options": "number"
            },
            "properties": [
              {
                "id": "custom.axisLabel",
                "value": "%"
              },
              {
                "id": "unit",
                "value": "percent"
              },
              {
                "id": "decimals"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 10,
        "w": 17,
        "x": 0,
        "y": 30
      },
      "id": 189,
      "options": {
        "barRadius": 0,
        "barWidth": 1,
        "fullHighlight": false,
        "groupWidth": 0.96,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "always",
        "stacking": "none",
        "tooltip": {
          "hideZeros": false,
          "mode": "single",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 300
      },
      "pluginVersion": "12.2.0",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "exemplar": false,
          "expr": "topk(10, process_cpu_percent{instance=~\"$instance\", process=~\"$process\"})",
          "format": "time_series",
          "instant": true,
          "interval": "",
          "legendFormat": "{{process}}",
          "range": false,
          "refId": "A"
        },
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "expr": "",
          "hide": false,
          "instant": false,
          "legendFormat": "__auto",
          "range": true,
          "refId": "B"
        }
      ],
      "title": "Per-Process CPU Usage",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": true,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "MB",
            "axisPlacement": "left",
            "fillOpacity": 86,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "lineWidth": 0,
            "scaleDistribution": {
              "log": 2,
              "type": "log"
            },
            "thresholdsStyle": {
              "mode": "line"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              },
              {
                "color": "red",
                "value": 5000
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byType",
              "options": "number"
            },
            "properties": [
              {
                "id": "unit",
                "value": "decmbytes"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 13,
        "w": 17,
        "x": 0,
        "y": 52
      },
      "id": 190,
      "options": {
        "barRadius": 0,
        "barWidth": 1,
        "fullHighlight": false,
        "groupWidth": 1,
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "orientation": "auto",
        "showValue": "auto",
        "stacking": "none",
        "tooltip": {
          "hideZeros": false,
          "mode": "multi",
          "sort": "none"
        },
        "xTickLabelRotation": 0,
        "xTickLabelSpacing": 200
      },
      "pluginVersion": "12.2.0",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "exemplar": false,
          "expr": "topk(10, process_memory_bytes{instance=~\"$instance\", process=~\"$process\"} / 1024 / 1024 )",
          "format": "time_series",
          "instant": true,
          "interval": "",
          "legendFormat": "{{process}}",
          "range": false,
          "refId": "A"
        },
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "expr": "",
          "hide": false,
          "instant": false,
          "legendFormat": "__auto",
          "range": true,
          "refId": "B"
        }
      ],
      "title": "Per-Process Memory Usage",
      "type": "barchart"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "axisSoftMax": 1,
            "axisSoftMin": 0,
            "barAlignment": -1,
            "barWidthFactor": 0.6,
            "drawStyle": "line",
            "fillOpacity": 0,
            "gradientMode": "opacity",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "insertNulls": false,
            "lineInterpolation": "stepAfter",
            "lineStyle": {
              "fill": "solid"
            },
            "lineWidth": 0,
            "pointSize": 2,
            "scaleDistribution": {
              "log": 2,
              "type": "symlog"
            },
            "showPoints": "always",
            "showValues": false,
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "decimals": 1,
          "mappings": [],
          "max": 1,
          "min": 0,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byType",
              "options": "number"
            },
            "properties": [
              {
                "id": "decimals"
              },
              {
                "id": "unit",
                "value": "decmbytes"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 13,
        "w": 24,
        "x": 0,
        "y": 65
      },
      "id": 196,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "hideZeros": false,
          "mode": "multi",
          "sort": "none"
        }
      },
      "pluginVersion": "12.2.0",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "exemplar": false,
          "expr": "topk(10, process_memory_bytes{instance=~\"$instance\", process=~\"$process\"} / 1024 / 1024 )",
          "format": "time_series",
          "instant": false,
          "interval": "1",
          "legendFormat": "{{process}}",
          "range": true,
          "refId": "A"
        }
      ],
      "title": "Per-Process Memory Usage (Time series)",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 10,
        "w": 24,
        "x": 0,
        "y": 78
      },
      "id": 191,
      "options": {
        "minVizHeight": 75,
        "minVizWidth": 75,
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "showThresholdLabels": false,
        "showThresholdMarkers": true,
        "sizing": "auto",
        "text": {
          "percentSize": 1
        }
      },
      "pluginVersion": "12.2.0",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "exemplar": false,
          "expr": "topk(15, process_count{instance=~\"$instance\", process=~\"$process\"})",
          "format": "time_series",
          "instant": true,
          "interval": "",
          "legendFormat": "{{process}}",
          "range": false,
          "refId": "A"
        },
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "expr": "",
          "hide": false,
          "instant": false,
          "legendFormat": "__auto",
          "range": true,
          "refId": "B"
        }
      ],
      "title": "Process_Count",
      "type": "gauge"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "axisSoftMax": 1,
            "axisSoftMin": 0,
            "barAlignment": -1,
            "barWidthFactor": 0.6,
            "drawStyle": "line",
            "fillOpacity": 0,
            "gradientMode": "opacity",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "insertNulls": false,
            "lineInterpolation": "stepAfter",
            "lineStyle": {
              "fill": "solid"
            },
            "lineWidth": 0,
            "pointSize": 2,
            "scaleDistribution": {
              "log": 2,
              "type": "symlog"
            },
            "showPoints": "always",
            "showValues": false,
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "decimals": 1,
          "mappings": [],
          "max": 1,
          "min": 0,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": 0
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byType",
              "options": "number"
            },
            "properties": [
              {
                "id": "decimals"
              }
            ]
          }
        ]
      },
      "gridPos": {
        "h": 12,
        "w": 24,
        "x": 0,
        "y": 88
      },
      "id": 197,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "hideZeros": false,
          "mode": "multi",
          "sort": "none"
        }
      },
      "pluginVersion": "12.2.0",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
          },
          "editorMode": "code",
          "exemplar": false,
          "expr": "topk(15, process_count{instance=~\"$instance\", process=~\"$process\"})",
          "format": "time_series",
          "instant": false,
          "interval": "1",
          "legendFormat": "{{process}}",
          "range": true,
          "refId": "A"
        }
      ],
      "title": "Process_Count",
      "type": "timeseries"
    }
  ],
  "preload": false,
  "refresh": "",
  "schemaVersion": 42,
  "tags": [],
  "templating": {
    "list": [
      {
        "current": {
          "text": "",
          "value": ""
        },
        "datasource": "prometheus",
        "definition": "label_values(origin_prometheus)",
        "includeAll": false,
        "label": "Origin_prom",
        "name": "origin_prometheus",
        "options": [],
        "query": "label_values(origin_prometheus)",
        "refresh": 1,
        "regex": "",
        "sort": 5,
        "type": "query"
      },
      {
        "current": {
          "text": "Acc-01_STG-Servers",
          "value": "Acc-01_STG-Servers"
        },
        "datasource": "prometheus",
        "definition": "label_values(node_uname_info{origin_prometheus=~\"$origin_prometheus\"}, job)",
        "includeAll": false,
        "label": "JOB",
        "name": "job",
        "options": [],
        "query": "label_values(node_uname_info{origin_prometheus=~\"$origin_prometheus\"}, job)",
        "refresh": 1,
        "regex": "",
        "sort": 5,
        "type": "query"
      },
      {
        "current": {
          "text": [
            "All"
          ],
          "value": [
            "$__all"
          ]
        },
        "datasource": "prometheus",
        "definition": "label_values(node_uname_info{origin_prometheus=~\"$origin_prometheus\",job=~\"$job\"}, nodename)",
        "includeAll": true,
        "label": "Host",
        "name": "hostname",
        "options": [],
        "query": "label_values(node_uname_info{origin_prometheus=~\"$origin_prometheus\",job=~\"$job\"}, nodename)",
        "refresh": 1,
        "regex": "",
        "sort": 5,
        "type": "query"
      },
      {
        "current": {
          "text": [
            "SGP-STG-VPN-BB2(172.19.23.11)"
          ],
          "value": [
            "SGP-STG-VPN-BB2(172.19.23.11)"
          ]
        },
        "datasource": "prometheus",
        "definition": "label_values(node_uname_info{origin_prometheus=~\"$origin_prometheus\",job=~\"$job\",nodename=~\"$hostname\"},instance)",
        "includeAll": false,
        "label": "Instance",
        "multi": true,
        "name": "node",
        "options": [],
        "query": "label_values(node_uname_info{origin_prometheus=~\"$origin_prometheus\",job=~\"$job\",nodename=~\"$hostname\"},instance)",
        "refresh": 1,
        "regex": "",
        "sort": 5,
        "type": "query"
      },
      {
        "current": {
          "text": [
            "All"
          ],
          "value": [
            "$__all"
          ]
        },
        "datasource": "prometheus",
        "definition": "label_values(node_network_info{origin_prometheus=~\"$origin_prometheus\",device!~'tap.*|veth.*|br.*|docker.*|virbr.*|cni.*|lo.*'},device)",
        "includeAll": true,
        "label": "NIC",
        "multi": true,
        "name": "device",
        "options": [],
        "query": "label_values(node_network_info{origin_prometheus=~\"$origin_prometheus\",device!~'tap.*|veth.*|br.*|docker.*|virbr.*|cni.*|lo.*'},device)",
        "refresh": 1,
        "regex": "",
        "sort": 1,
        "type": "query"
      },
      {
        "auto": false,
        "auto_count": 100,
        "auto_min": "10s",
        "current": {
          "text": "30s",
          "value": "30s"
        },
        "label": "Interval",
        "name": "interval",
        "options": [
          {
            "selected": true,
            "text": "30s",
            "value": "30s"
          },
          {
            "selected": false,
            "text": "1m",
            "value": "1m"
          },
          {
            "selected": false,
            "text": "2m",
            "value": "2m"
          },
          {
            "selected": false,
            "text": "3m",
            "value": "3m"
          },
          {
            "selected": false,
            "text": "5m",
            "value": "5m"
          },
          {
            "selected": false,
            "text": "10m",
            "value": "10m"
          },
          {
            "selected": false,
            "text": "30m",
            "value": "30m"
          }
        ],
        "query": "30s,1m,2m,3m,5m,10m,30m",
        "refresh": 2,
        "type": "interval"
      },
      {
        "current": {
          "text": "/",
          "value": "/"
        },
        "datasource": "prometheus",
        "definition": "query_result(topk(1,sort_desc (max(node_filesystem_size_bytes{origin_prometheus=~\"$origin_prometheus\",instance=~'$node',fstype=~\"ext.?|xfs\",mountpoint!~\".*pods.*\"}) by (mountpoint))))",
        "hide": 2,
        "includeAll": false,
        "label": "maxmount",
        "name": "maxmount",
        "options": [],
        "query": "query_result(topk(1,sort_desc (max(node_filesystem_size_bytes{origin_prometheus=~\"$origin_prometheus\",instance=~'$node',fstype=~\"ext.?|xfs\",mountpoint!~\".*pods.*\"}) by (mountpoint))))",
        "refresh": 2,
        "regex": "/.*\\\"(.*)\\\".*/",
        "sort": 5,
        "type": "query"
      },
      {
        "current": {
          "text": "ip-172-19-23-11.ap-southeast-1.compute.internal",
          "value": "ip-172-19-23-11.ap-southeast-1.compute.internal"
        },
        "datasource": "prometheus",
        "definition": "label_values(node_uname_info{origin_prometheus=~\"$origin_prometheus\",job=~\"$job\",instance=~\"$node\"}, nodename)",
        "hide": 2,
        "includeAll": false,
        "label": "show_hostname",
        "name": "show_hostname",
        "options": [],
        "query": "label_values(node_uname_info{origin_prometheus=~\"$origin_prometheus\",job=~\"$job\",instance=~\"$node\"}, nodename)",
        "refresh": 1,
        "regex": "",
        "sort": 5,
        "type": "query"
      },
      {
        "current": {
          "text": "",
          "value": ""
        },
        "datasource": {
          "type": "prometheus",
          "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
        },
        "definition": "label_values(node_uname_info)",
        "includeAll": false,
        "label": "Instance",
        "name": "instance",
        "options": [],
        "query": "label_values(node_uname_info)",
        "refresh": 2,
        "type": "query"
      },
      {
        "current": {
          "text": "",
          "value": ""
        },
        "datasource": {
          "type": "prometheus",
          "uid": "f244fa0b-69c6-4a52-bb76-e1bfd4fdae37"
        },
        "definition": "label_values(process_cpu_percent)",
        "includeAll": false,
        "label": "Process",
        "name": "process",
        "options": [],
        "query": "label_values(process_cpu_percent)",
        "refresh": 2,
        "type": "query"
      }
    ]
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {
    "refresh_intervals": [
      "15s",
      "30s",
      "1m",
      "5m",
      "15m",
      "30m"
    ]
  },
  "timezone": "browser",
  "title": "Process CPU & Memory Monitoring",
  "uid": "1a95f675-7aee-4302-a2cb-4c83b5410ce7",
  "version": 2
}
