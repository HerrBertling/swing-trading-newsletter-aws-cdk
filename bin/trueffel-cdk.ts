#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { TrueffelCdkStack } from '../lib/trueffel-cdk-stack';

const app = new cdk.App();
new TrueffelCdkStack(app, 'TrueffelCdkStack');
