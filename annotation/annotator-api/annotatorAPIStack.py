from os import getenv
from platform import architecture
from aws_cdk import (
    Stack,
    Duration,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns  as ecs_patterns,
    aws_elasticloadbalancingv2 as elb,
    aws_autoscaling as autoscaling,
    aws_route53 as route53,
    aws_rds as rds
)

from dotenv import load_dotenv

from constructs import Construct

class AnnotatorAPIStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        load_dotenv()

        self.vpc_name = getenv("vpc_name")
        self.zone_name = getenv("zone_name")
        self.domain_name = getenv("domain_name")
        self.service_cluster_min = int(getenv("service_cluster_min"))
        self.service_cluster_max = int(getenv("service_cluster_max"))
        self.api_service_min = int(getenv("api_service_min"))
        self.api_service_max= int(getenv("api_service_max"))
        self.db_cluster_name = getenv("db_cluster_name")

        self.vpc = ec2.Vpc(self, self.vpc_name)
        self.hosted_zone = route53.HostedZone.from_lookup(self, id="AnnotatorZone", domain_name=self.zone_name)
        
        self.service_cluster = ecs.Cluster(self, "AnnotatorCluster",
        vpc=self.vpc)

        # self.service_cluster_image = ecs.BottleRocketImage(architecture=ecs.AmiHardwareType.ARM)
        # TODO: BottleRocket is more efficient than AL2, but ECS does not properly support it on ARM (yet)
        self.service_cluster_image = ecs.EcsOptimizedImage.amazon_linux2(hardware_type=ecs.AmiHardwareType.STANDARD)
        # self.service_cluster_instance_type = ec2.InstanceType("t3a.small")

        # self.auto_scaling_group = autoscaling.AutoScalingGroup(
        #     self, "ASG", vpc=self.vpc, 
        #     instance_type=self.service_cluster_instance_type,
        #     machine_image=self.service_cluster_image,
        #     min_capacity=self.service_cluster_min,
        #     max_capacity=self.service_cluster_max,
        #     max_instance_lifetime=Duration.days(7)
        # )

        # self.capacity_provider = ecs.AsgCapacityProvider(self, "AsgCapacityProvider", auto_scaling_group=self.auto_scaling_group)

        # self.service_cluster.add_asg_capacity_provider(self.capacity_provider)

        self.api_container_image = ecs.ContainerImage.from_asset("./api_stack/")

        # self.api_service = ecs_patterns.ApplicationLoadBalancedEc2Service(self, "AnnotatorAPIService",
        #     cluster=self.service_cluster,
        #     cpu=1024, memory_limit_mib=1024,
        #     public_load_balancer=True,
        #     protocol=elb.ApplicationProtocol.HTTPS,
        #     #redirect_http=True,
        #     target_protocol=elb.ApplicationProtocol.HTTP,
        #     task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
        #         image=self.api_container_image,
        #         container_port=80),
        #     domain_name=self.domain_name,
        #     domain_zone=self.hosted_zone
        # )

        self.api_service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "AnnotatorAPIService",
            cluster=self.service_cluster,
            cpu=1024, memory_limit_mib=2048,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=self.api_container_image
            ),
            public_load_balancer=True,
            protocol=elb.ApplicationProtocol.HTTPS,
            target_protocol=elb.ApplicationProtocol.HTTP,
            domain_name=self.domain_name,
            domain_zone=self.hosted_zone
        )

        self.api_service.target_group.configure_health_check(path="/health")

        self.api_scalable_target = self.api_service.service.auto_scale_task_count(
            min_capacity=self.api_service_min, max_capacity=self.api_service_max
        )

        self.api_scalable_target.scale_on_cpu_utilization("CpuScaling",
            target_utilization_percent=80
        )

        self.api_scalable_target.scale_on_memory_utilization("MemoryScaling",
            target_utilization_percent=80
        )

        self.db_cluster = rds.DatabaseCluster(self, "AnnotationDatabase",
            engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_3_01_0),
            instance_props=rds.InstanceProps(vpc=self.vpc, instance_type=ec2.InstanceType("t4g.medium"),
            allow_major_version_upgrade=False,
            auto_minor_version_upgrade=True,
            publicly_accessible=True,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)),
            cluster_identifier=self.db_cluster_name,
            storage_encrypted=True
        )