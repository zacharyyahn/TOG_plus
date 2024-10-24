from attack_utils.target_utils import generate_attack_targets
import numpy as np
import torch

def tog_attention(victim, x_query, n_iter=10, eps=8/255., eps_iter=2/255., attn_lr=0.01, vis=False, mode="untargeted", meta=None):
    attack_modes = {
        "untargeted":victim.compute_object_untargeted_gradient,
        "vanishing":victim.compute_object_vanishing_gradient,
        "fabrication":victim.compute_object_fabrication_gradient
    }
    
    if vis:
        etas = []
        eta_grads = []
        map_grads = []
        maps = []
   
    # Get detections and initialize eta and attn. Sometimes there is additional metadata to pass in
    detections_query = None
    if meta == None:
        detections_query = victim.detect(x_query, conf_threshold=victim.confidence_thresh_default)
    else:
        detections_query = victim.detect(x_query, meta=meta)
        detections_query[0]['meta'] = meta # also want to pass in meta here so that the gradient functions can access it
            
    init_min = torch.min(x_query).item()
    init_max = torch.max(x_query).item()
    
    eps_iter = eps_iter * init_max
    eps = eps * init_max
    
    eta = np.random.uniform(-eps, eps, size=x_query.shape)
    attn_map = np.ones((x_query.shape))
    
    # initialize attention maps with bounding boxes. Area inside the box gets a 1.5 effect multiplier
#     for det in detections_query:
#         effect = np.ones(attn_map.shape)
#         xmin, ymin, xmax, ymax = int(det[-4]), int(det[-3]), int(det[-2]), int(det[-1])
#         effect[0, ymin:ymax, xmin:xmax, :] = 1.5
#         attn_map = np.multiply(attn_map, effect)
    
    # Make the first adversarial example
    x_adv = x_query + np.multiply(attn_map, eta)

    #x_adv = x_query + np.multiply(attn_map, eta)
    for i in range(n_iter):
        
        # save for visualization
        if vis:
            etas.append(eta.copy())
            maps.append(attn_map.copy())

        # first get the gradient for x_adv
        grad = attack_modes[mode](x_adv, x_query, detections = detections_query, norm=True)
        
        # compute the two partials. Simple multiplication because this is elementwise, not matmul
        eta_grad = np.multiply(grad, attn_map)
        attn_map_grad = np.multiply(grad, eta)# + np.random.normal(0, 0.01, (x_query.shape))
        
        # update eta
        signed_eta_grad = np.sign(eta_grad)
        eta -= eps_iter * signed_eta_grad
        eta = np.clip(eta, -eps, eps)
        
        # update attention
        norm_attn_map_grad = (attn_map_grad - np.mean(attn_map_grad)) / np.std(attn_map_grad)
        attn_map -= attn_lr * norm_attn_map_grad
        
        # save for visualization
        if vis:
            eta_grads.append(eta_grad.copy())
            map_grads.append(attn_map_grad.copy())
    
        # make the next iteration of x_adv
        #x_adv = x_query + np.multiply(attn_map, eta)
        x_adv = np.clip(x_query + np.multiply(attn_map, eta), init_min, init_max)
    
    final_pert = x_adv - x_query
    final_pert = np.clip(final_pert, -eps, eps)
    x_adv = np.clip(x_query + final_pert, init_min, init_max)
    
    if vis: return x_adv, etas, eta_grads, map_grads, maps
    return x_adv

def tog_untargeted_class(victim, x_query, n_iter=10, eps=8/255., eps_iter=2/255., mode=None):
    detections_query = victim.detect(x_query, conf_threshold=victim.confidence_thresh_default)
    eta = np.random.uniform(-eps, eps, size=x_query.shape)
    x_adv = np.clip(x_query + eta, 0.0, 1.0)
    for _ in range(n_iter):
        grad = victim.compute_object_untargeted_class_gradient(x_adv, detections=detections_query)
        signed_grad = np.sign(grad)
        x_adv -= eps_iter * signed_grad
        eta = np.clip(x_adv - x_query, -eps, eps)
        x_adv = np.clip(x_query + eta, 0.0, 1.0)
    return x_adv              

def tog_vanishing(victim, x_query, n_iter=10, eps=8/255., eps_iter=2/255., mode=None):
    eta = np.random.uniform(-eps, eps, size=x_query.shape)
    x_adv = np.clip(x_query + eta, 0.0, 1.0)
    for _ in range(n_iter):
        grad = victim.compute_object_vanishing_gradient(x_adv)
        signed_grad = np.sign(grad)
        x_adv -= eps_iter * signed_grad
        eta = np.clip(x_adv - x_query, -eps, eps)
        x_adv = np.clip(x_query + eta, 0.0, 1.0)
    return x_adv


def tog_fabrication(victim, x_query, n_iter=10, eps=8/255., eps_iter=2/255., mode=None):
    eta = np.random.uniform(-eps, eps, size=x_query.shape)
    x_adv = np.clip(x_query + eta, 0.0, 1.0)
    for _ in range(n_iter):
        grad = victim.compute_object_fabrication_gradient(x_adv)
        signed_grad = np.sign(grad)
        x_adv -= eps_iter * signed_grad
        eta = np.clip(x_adv - x_query, -eps, eps)
        x_adv = np.clip(x_query + eta, 0.0, 1.0)
    return x_adv


def tog_mislabeling(victim, x_query, target, n_iter=10, eps=8/255., eps_iter=2/255.):
    detections_query = victim.detect(x_query, conf_threshold=victim.confidence_thresh_default)
    detections_target = generate_attack_targets(detections_query, confidence_threshold=victim.confidence_thresh_default,
                                                mode=target)
    eta = np.random.uniform(-eps, eps, size=x_query.shape)
    x_adv = np.clip(x_query + eta, 0.0, 1.0)
    for _ in range(n_iter):
        grad = victim.compute_object_mislabeling_gradient(x_adv, detections=detections_target)
        signed_grad = np.sign(grad)
        x_adv -= eps_iter * signed_grad
        eta = np.clip(x_adv - x_query, -eps, eps)
        x_adv = np.clip(x_query + eta, 0.0, 1.0)
    return x_adv


def tog_untargeted(victim, x_query, n_iter=10, eps=8/255., eps_iter=2/255., mode=None, meta=None):
    init_min = torch.min(x_query).item()
    init_max = torch.max(x_query).item()
    
    eps_iter = eps_iter * init_max
    eps = eps * init_max
    
    if meta == None:
        detections_query = victim.detect(x_query, conf_threshold=victim.confidence_thresh_default)
    else:
        detections_query = victim.detect(x_query, meta=meta)
        detections_query[0]["meta"] = meta
    eta = np.random.uniform(-eps, eps, size=x_query.shape)
    
    x_adv = np.clip(x_query + eta, init_min, init_max)
    for _ in range(n_iter):
        grad = victim.compute_object_untargeted_gradient(x_adv, detections=detections_query)
        signed_grad = np.sign(grad)
        x_adv -= eps_iter * signed_grad
        eta = np.clip(x_adv - x_query, -eps, eps)
        x_adv = np.clip(x_query + eta, init_min, init_max)
    return x_adv

def tog_untargeted_viz(victim, x_query, n_iter=10, eps=8/255., eps_iter=2/255.):
    etas = []
    grads = []
    
    detections_query = victim.detect(x_query, conf_threshold=victim.confidence_thresh_default)
    eta = np.random.uniform(-eps, eps, size=x_query.shape)
    etas.append(eta)
    x_adv = np.clip(x_query + eta, 0.0, 1.0)
    for _ in range(n_iter):
        grad = victim.compute_object_untargeted_gradient(x_adv, detections=detections_query)
        grads.append(grad)
        signed_grad = np.sign(grad)
        x_adv -= eps_iter * signed_grad
        eta = np.clip(x_adv - x_query, -eps, eps)
        etas.append(eta)
        x_adv = np.clip(x_query + eta, 0.0, 1.0)
    
    return x_adv, etas, grads
