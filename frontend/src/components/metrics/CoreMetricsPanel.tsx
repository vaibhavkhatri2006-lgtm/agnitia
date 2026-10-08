import React from 'react';
import { MetricCard } from './MetricCard';
import { Metric } from '../../types/models';

interface CoreMetricsProps {
  accessibility: Metric;
  gap: Metric;
  equity: Metric;
  confidence: Metric;
  realityGap: Metric;
  servicePressure: Metric;
  loading?: boolean;
}

export const CoreMetricsPanel: React.FC<CoreMetricsProps> = (props) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      <MetricCard metric={props.accessibility} loading={props.loading} />
      <MetricCard metric={props.gap} loading={props.loading} trend="down" trendValue="2% vs last month" />
      <MetricCard metric={props.equity} loading={props.loading} />
      <MetricCard metric={props.confidence} loading={props.loading} />
      <MetricCard metric={props.realityGap} loading={props.loading} />
      <MetricCard metric={props.servicePressure} loading={props.loading} trend="up" trendValue="High demand" />
    </div>
  );
};
