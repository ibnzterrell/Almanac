from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns  as ecs_patterns,
    aws_rds as rds
)
from constructs import Construct

class AnnotatorAPIStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(self, "AnnotatorVPC")
        self.cluster = ecs.Cluster(self, "AnnotatorCluster",
        vpc=self.vpc)
        self.api_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "AnnotatorAPIService",
            cluster=self.cluster,
            cpu=256, memory_limit_mib=512,
            public_load_balancer=True,desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("./api_stack/"))
        )

        self.api_scalable_target = self.api_service.service.auto_scale_task_count(
            min_capacity=1, max_capacity=4
        )

        self.api_scalable_target.scale_on_cpu_utilization("CpuScaling",
            target_utilization_percent=80
        )

        self.api_scalable_target.scale_on_memory_utilization("MemoryScaling",
            target_utilization_percent=80
        )