import type {AreaChartSeries} from 'sentry/components/charts/areaChart';
import XAxis from 'sentry/components/charts/components/xAxis';
import AreaSeries from 'sentry/components/charts/series/areaSeries';
import type {SessionApiResponse} from 'sentry/types';
import {lightTheme as theme} from 'sentry/utils/theme';
import {
  getMetricAlertChartOption,
  MetricChartData,
  transformSessionResponseToSeries,
} from 'sentry/views/alerts/rules/details/metricChartOption';

import {DEFAULT_FONT_FAMILY, slackChartSize} from './slack';
import {ChartType, RenderDescriptor} from './types';

const discoverxAxis = XAxis({
  theme,
  // @ts-expect-error Not sure whats wrong with boundryGap type
  boundaryGap: true,
  splitNumber: 3,
  isGroupedByDate: true,
  axisLabel: {fontSize: 11, fontFamily: DEFAULT_FONT_FAMILY},
});

function transformAreaSeries(series: AreaChartSeries[]) {
  return series.map(({seriesName, data, ...otherSeriesProps}) =>
    AreaSeries({
      name: seriesName,
      data: data.map(({name, value}) => [name, value]),
      lineStyle: {
        opacity: 1,
        width: 0.4,
      },
      areaStyle: {
        opacity: 1.0,
      },
      animation: false,
      animationThreshold: 1,
      animationDuration: 0,
      ...otherSeriesProps,
    })
  );
}

export const metricAlertCharts: RenderDescriptor<ChartType>[] = [];

metricAlertCharts.push({
  key: ChartType.SLACK_METRIC_ALERT_EVENTS,
  getOption: (data: MetricChartData) => {
    const {chartOption} = getMetricAlertChartOption(data);

    return {
      ...chartOption,
      backgroundColor: theme.background,
      series: transformAreaSeries(chartOption.series),
      xAxis: discoverxAxis,
    };
  },
  ...slackChartSize,
});

interface MetricAlertSessionData extends Omit<MetricChartData, 'timeseriesData'> {
  sessionResponse: SessionApiResponse;
}

metricAlertCharts.push({
  key: ChartType.SLACK_METRIC_ALERT_SESSIONS,
  getOption: (data: MetricAlertSessionData) => {
    const {sessionResponse, rule, ...rest} = data;
    const {chartOption} = getMetricAlertChartOption({
      ...rest,
      rule,
      timeseriesData: transformSessionResponseToSeries(sessionResponse, rule),
    });

    return {
      ...chartOption,
      backgroundColor: theme.background,
      series: transformAreaSeries(chartOption.series),
      xAxis: discoverxAxis,
    };
  },
  ...slackChartSize,
});
