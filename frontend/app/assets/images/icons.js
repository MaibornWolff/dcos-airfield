import Vue from 'vue';

import { library } from '@fortawesome/fontawesome-svg-core';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

import {
    faBan,
    faBox,
    faBuilding,
    faCheck,
    faCog,
    faComment,
    faCommentSlash,
    faDownload,
    faExclamationTriangle,
    faEye,
    faEyeSlash,
    faHdd,
    faHome,
    faIndustry,
    faInfoCircle,
    faLaptop,
    faLaptopCode,
    faList,
    faLockOpen,
    faMicrochip,
    faMoneyBillAlt,
    faPlay,
    faPlayCircle,
    faPlus,
    faQuestionCircle,
    faRegistered,
    faSave,
    faSlidersH,
    faSpinner,
    faStop,
    faSync,
    faTrashAlt,
    faUpload,
    faWindowRestore
} from '@fortawesome/free-solid-svg-icons';

import {
    faPython
} from '@fortawesome/free-brands-svg-icons';

library.add(
    faBan,
    faBox,
    faBuilding,
    faCheck,
    faCog,
    faComment,
    faCommentSlash,
    faDownload,
    faExclamationTriangle,
    faEye,
    faEyeSlash,
    faHdd,
    faHome,
    faIndustry,
    faInfoCircle,
    faLaptop,
    faLaptopCode,
    faList,
    faLockOpen,
    faMicrochip,
    faMoneyBillAlt,
    faPlay,
    faPlayCircle,
    faPlus,
    faPython,
    faQuestionCircle,
    faRegistered,
    faSave,
    faSlidersH,
    faSpinner,
    faStop,
    faSync,
    faTrashAlt,
    faUpload,
    faWindowRestore
);

Vue.component('fa', FontAwesomeIcon);