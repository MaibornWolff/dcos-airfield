import Vue from 'vue';

import { library } from '@fortawesome/fontawesome-svg-core';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

import {
    faHome,
    faBuilding,
    faIndustry,
    faQuestionCircle,
    faPlus,
    faSpinner,
    faInfoCircle,
    faCheck,
    faRegistered,
    faSync,
    faPlay,
    faPlayCircle,
    faStop,
    faTrashAlt,
    faList,
    faBox,
    faSlidersH,
    faLockOpen,
    faExclamationTriangle,
    faCog,
    faUpload,
    faDownload
} from '@fortawesome/free-solid-svg-icons';

import {
    faPython
} from '@fortawesome/free-brands-svg-icons';

library.add(
    faHome,
    faBuilding,
    faIndustry,
    faQuestionCircle,
    faPlus,
    faSpinner,
    faInfoCircle,
    faCheck,
    faRegistered,
    faSync,
    faPlay,
    faPlayCircle,
    faStop,
    faTrashAlt,
    faList,
    faBox,
    faSlidersH,
    faPython,
    faLockOpen,
    faExclamationTriangle,
    faCog,
    faUpload,
    faDownload
);

Vue.component('fa', FontAwesomeIcon);