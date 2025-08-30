# CFMP 自动扩缩容

## 快速部署
```bash
./start-k8s-simple.sh
```

## 核心功能
- **自动扩缩容**: 基于 CPU/内存自动调整副本数
- **高可用保障**: Pod 中断预算确保服务稳定性

## 扩缩容规则
| 服务 | 最小副本 | 最大副本 | CPU阈值 | 内存阈值 |
|------|---------|---------|---------|----------|
| 订单服务 | 2 | 10 | 70% | 80% |
| 支付服务 | 2 | 8 | 65% | 75% |
| 通知服务 | 1 | 6 | 75% | 80% |

## 常用命令
```bash
# 查看状态
kubectl -n cfmp-order get pods,hpa

# 手动扩缩容
kubectl -n cfmp-order scale deployment order-service --replicas=5

# 查看日志
kubectl -n cfmp-order logs deployment/order-service

# 查看资源使用
kubectl top pods -n cfmp-order
```

## 压力测试
使用 Apache JMeter 测试以下端点：
- 订单服务: `http://localhost:30001/health/`
- 支付服务: `http://localhost:30002/health/`
- 通知服务: `http://localhost:30003/health/`

## 配置文件
- `k8s/hpa.yaml` - 自动扩缩容配置
- `k8s/pdb.yaml` - Pod中断预算
- `k8s/circuit-breaker.yaml` - 基础配置