import React, {useMemo} from 'react';

import Button from 'sentry/components/button';
import Clipboard from 'sentry/components/clipboard';
import {useReplayContext} from 'sentry/components/replays/replayContext';
import {IconLink} from 'sentry/icons';
import {t} from 'sentry/locale';
import createUrlToShare from 'sentry/utils/replays/createUrlToShare';

function ShareButton() {
  const {currentTime} = useReplayContext();
  const urlToShare = useMemo(() => {
    return createUrlToShare(currentTime);
  }, [currentTime]);

  // `hideUnsupported` calls `document.queryCommandSupported?.('copy')` which
  // results in a render issue on chrome v102 & v103. The issue is that
  // `~ footer { display:none; }` wasn't taking effect in the rendered output.
  return (
    <Clipboard value={urlToShare}>
      <Button icon={<IconLink />} size="small">
        {t('Share')}
      </Button>
    </Clipboard>
  );
}

export default ShareButton;
