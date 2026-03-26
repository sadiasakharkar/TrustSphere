import React from 'react';
import EmptyState from './soc/EmptyState';
import Layout from './Layout';
import PageContainer from './soc/PageContainer';

export default class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch() {}

  render() {
    if (this.state.hasError) {
      return (
        <Layout>
          <PageContainer>
            <EmptyState
              title="Workspace temporarily recovering"
              detail="TrustSphere retained the session but one view failed to render. Refresh the page to resume the SOC workflow."
            />
          </PageContainer>
        </Layout>
      );
    }
    return this.props.children;
  }
}
